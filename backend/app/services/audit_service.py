import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request
from ..models.audit_log import AuditLog, SecurityEvent, ActionType, SeverityLevel
from ..models.user import User
from ..core.database import get_db
import json
import uuid
import asyncio

logger = logging.getLogger(__name__)

class AuditService:
    """Сервис для аудит логирования"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        action: ActionType,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: SeverityLevel = SeverityLevel.LOW,
        status: str = "success",
        error_message: Optional[str] = None,
        request: Optional[Request] = None,
        duration_ms: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Логирование действия пользователя"""
        
        try:
            # Извлекаем информацию из запроса
            ip_address = None
            user_agent = None
            session_id = None
            
            if request and hasattr(request, "headers"):
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                session_id = getattr(request, "cookies", {}).get("session_id") if hasattr(request, "cookies") else None
            
            # Создаем запись аудит лога
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                description=description,
                details=details,
                severity=severity,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
                request_id=request_id or str(uuid.uuid4())
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.info(f"Audit log created: {action} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            self.db.rollback()
            raise
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        threat_level: SeverityLevel = SeverityLevel.MEDIUM,
        request: Optional[Request] = None
    ) -> SecurityEvent:
        """Логирование события безопасности"""
        
        try:
            # Извлекаем информацию из запроса
            ip_address = None
            user_agent = None
            
            if request and hasattr(request, "headers"):
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
            
            # Создаем запись события безопасности
            security_event = SecurityEvent(
                user_id=user_id,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description,
                details=details,
                threat_level=threat_level
            )
            
            self.db.add(security_event)
            self.db.commit()
            self.db.refresh(security_event)
            
            logger.warning(f"Security event logged: {event_type} for user {user_id}")
            return security_event
            
        except Exception as e:
            logger.error(f"Failed to create security event: {e}")
            self.db.rollback()
            raise
    
    def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[ActionType] = None,
        severity_filter: Optional[SeverityLevel] = None
    ) -> List[AuditLog]:
        """Получение аудит логов пользователя"""
        
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        if severity_filter:
            query = query.filter(AuditLog.severity == severity_filter)
        
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_security_events(
        self,
        limit: int = 100,
        offset: int = 0,
        threat_level_filter: Optional[SeverityLevel] = None,
        status_filter: Optional[str] = None
    ) -> List[SecurityEvent]:
        """Получение событий безопасности"""
        
        query = self.db.query(SecurityEvent)
        
        if threat_level_filter:
            query = query.filter(SecurityEvent.threat_level == threat_level_filter)
        
        if status_filter:
            query = query.filter(SecurityEvent.status == status_filter)
        
        return query.order_by(SecurityEvent.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_audit_statistics(
        self,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Получение статистики аудит логов"""
        
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(AuditLog).filter(AuditLog.created_at >= start_date)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        # Общая статистика
        total_actions = query.count()
        
        # Статистика по типам действий
        action_stats = (
            query.with_entities(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .all()
        )
        
        # Статистика по статусам
        status_stats = (
            query.with_entities(AuditLog.status, func.count(AuditLog.id))
            .group_by(AuditLog.status)
            .all()
        )
        
        # Статистика по уровням серьезности
        severity_stats = (
            query.with_entities(AuditLog.severity, func.count(AuditLog.id))
            .group_by(AuditLog.severity)
            .all()
        )
        
        return {
            "total_actions": total_actions,
            "action_breakdown": dict(action_stats),
            "status_breakdown": dict(status_stats),
            "severity_breakdown": dict(severity_stats),
            "period_days": days
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Получение IP адреса клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For") if hasattr(request, "headers") else None
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP") if hasattr(request, "headers") else None
        if real_ip:
            return real_ip
        
        # Возвращаем IP из request
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

# Декоратор для автоматического логирования действий
def audit_action(
    action: ActionType,
    resource: Optional[str] = None,
    severity: SeverityLevel = SeverityLevel.LOW
):
    """Декоратор для автоматического логирования действий"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем request и user из аргументов
            request = None
            user = None
            db = None
            
            for arg in args:
                if hasattr(arg, 'headers'):  # Request object
                    request = arg
                elif hasattr(arg, 'id') and hasattr(arg, 'email'):  # User object
                    user = arg
                elif hasattr(arg, 'query'):  # Database session
                    db = arg
            
            # Если не нашли db в аргументах, получаем из зависимости
            if not db:
                db = next(get_db())
            
            audit_service = AuditService(db)
            start_time = datetime.utcnow()
            
            try:
                # Выполняем функцию
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Логируем успешное выполнение
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                audit_service.log_action(
                    action=action,
                    user_id=user.id if user else None,
                    resource=resource,
                    description=f"Successfully executed {func.__name__}",
                    severity=severity,
                    status="success",
                    request=request,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                audit_service.log_action(
                    action=action,
                    user_id=user.id if user else None,
                    resource=resource,
                    description=f"Failed to execute {func.__name__}",
                    severity=SeverityLevel.HIGH,
                    status="error",
                    error_message=str(e),
                    request=request,
                    duration_ms=duration_ms
                )
                raise
        return wrapper
    return decorator

# Утилиты для быстрого логирования
def log_user_login(db: Session, user: User, request: Request, success: bool = True):
    """Логирование входа пользователя"""
    audit_service = AuditService(db)
    return audit_service.log_action(
        action=ActionType.LOGIN,
        user_id=user.id if success else None,
        description=f"User {'successfully' if success else 'failed to'} login",
        severity=SeverityLevel.MEDIUM if success else SeverityLevel.HIGH,
        status="success" if success else "failed",
        request=request
    )

def log_user_logout(db: Session, user: User, request: Request):
    """Логирование выхода пользователя"""
    audit_service = AuditService(db)
    return audit_service.log_action(
        action=ActionType.LOGOUT,
        user_id=user.id,
        description="User logout",
        request=request
    )

def log_chat_message(db: Session, user: User, message_id: str, request: Request):
    """Логирование отправки сообщения в чат"""
    audit_service = AuditService(db)
    return audit_service.log_action(
        action=ActionType.CHAT_MESSAGE,
        user_id=user.id,
        resource="chat_message",
        resource_id=message_id,
        description="User sent chat message",
        request=request
    )

def log_file_upload(db: Session, user: User, file_info: Dict[str, Any], request: Request):
    """Логирование загрузки файла"""
    audit_service = AuditService(db)
    return audit_service.log_action(
        action=ActionType.FILE_UPLOAD,
        user_id=user.id,
        resource="file",
        resource_id=file_info.get("id"),
        description=f"User uploaded file: {file_info.get('filename')}",
        details=file_info,
        request=request
    )

def log_security_incident(db: Session, event_type: str, user_id: Optional[int], request: Request, details: Optional[Dict] = None):
    """Логирование инцидента безопасности"""
    audit_service = AuditService(db)
    return audit_service.log_security_event(
        event_type=event_type,
        user_id=user_id,
        description=f"Security incident: {event_type}",
        details=details,
        threat_level=SeverityLevel.HIGH,
        request=request
    )

# Глобальный экземпляр для использования в API
audit_service = None

def get_audit_service(db: Session = None):
    """Получить экземпляр AuditService"""
    global audit_service
    if audit_service is None or db is not None:
        audit_service = AuditService(db)
    return audit_service
