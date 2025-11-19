"""
Админ-панель API - полноценная система управления
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..models.audit_log import AuditLog, SecurityEvent, ActionType, SeverityLevel
from ..schemas.user import User as UserSchema
from ..services.auth_service import AuthService
from ..core.admin_security import admin_security
# Импорт не нужен, используем auth_service.get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
auth_service = AuthService()

def get_current_admin(current_user: User = Depends(auth_service.get_current_user)) -> User:
    """Получение текущего администратора с проверкой прав"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора"
        )
    return current_user


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получение статистики для админ-панели"""
    try:
        # Статистика пользователей
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        premium_users = db.query(User).filter(User.is_premium == True).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        
        # Статистика чатов
        total_sessions = db.query(ChatSession).count()
        total_messages = db.query(ChatMessage).count()
        
        # Статистика за последние 24 часа
        yesterday = datetime.utcnow() - timedelta(days=1)
        new_users_24h = db.query(User).filter(User.created_at >= yesterday).count()
        new_sessions_24h = db.query(ChatSession).filter(ChatSession.created_at >= yesterday).count()
        new_messages_24h = db.query(ChatMessage).filter(ChatMessage.created_at >= yesterday).count()
        
        # Статистика безопасности
        security_events = db.query(SecurityEvent).filter(
            SecurityEvent.created_at >= yesterday
        ).count()
        
        # Топ пользователи по активности
        top_users = db.query(User).join(ChatSession).group_by(User.id).order_by(
            db.func.count(ChatSession.id).desc()
        ).limit(5).all()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "premium": premium_users,
                "admins": admin_users,
                "new_24h": new_users_24h
            },
            "chats": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "new_sessions_24h": new_sessions_24h,
                "new_messages_24h": new_messages_24h
            },
            "security": {
                "events_24h": security_events
            },
            "top_users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_premium": bool(user.is_premium),
                    "is_admin": bool(user.is_admin),
                    "created_at": user.created_at.isoformat()
                }
                for user in top_users
            ]
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статистики"
        )


@router.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получение списка пользователей с фильтрацией"""
    try:
        query = db.query(User)
        
        # Фильтрация
        if search:
            query = query.filter(
                (User.email.contains(search)) |
                (User.username.contains(search)) |
                (User.full_name.contains(search))
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            
        if is_premium is not None:
            query = query.filter(User.is_premium == is_premium)
        
        # Пагинация
        total = query.count()
        users = query.offset((page - 1) * limit).limit(limit).all()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": bool(user.is_active),
                    "is_premium": bool(user.is_premium),
                    "is_admin": bool(user.is_admin),
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.updated_at.isoformat() if user.updated_at else None
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка пользователей"
        )


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получение детальной информации о пользователе"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Статистика пользователя
        user_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).count()
        user_messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.user_id == user_id
        ).count()
        
        # Последние активности
        recent_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(5).all()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "legal_form": user.legal_form,
                "inn": user.inn,
                "ogrn": user.ogrn,
                "is_active": bool(user.is_active),
                "is_premium": bool(user.is_premium),
                "is_admin": bool(user.is_admin),
                "subscription_type": user.subscription_type,
                "subscription_expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            },
            "stats": {
                "total_sessions": user_sessions,
                "total_messages": user_messages
            },
            "recent_sessions": [
                {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
                for session in recent_sessions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения деталей пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения информации о пользователе"
        )


@router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Активация/деактивация пользователя"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Нельзя деактивировать себя
        if user.id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя деактивировать собственный аккаунт"
            )
        
        user.is_active = not user.is_active
        db.commit()
        
        # Логируем действие
        from ..services.audit_service import get_audit_service
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="user",
            resource_id=user_id,
            description=f"Изменен статус пользователя {user.email}: {'активирован' if user.is_active else 'деактивирован'}",
            severity=SeverityLevel.HIGH,
            status="success"
        )
        
        return {
            "message": f"Пользователь {'активирован' if user.is_active else 'деактивирован'}",
            "user_id": user_id,
            "is_active": user.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка изменения статуса пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка изменения статуса пользователя"
        )


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action_type: Optional[str] = None,
    user_id: Optional[int] = None,
    severity: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получение логов аудита"""
    try:
        query = db.query(AuditLog)
        
        # Фильтрация
        if action_type:
            query = query.filter(AuditLog.action == action_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        # Сортировка по времени (новые сначала)
        query = query.order_by(AuditLog.created_at.desc())
        
        # Пагинация
        total = query.count()
        logs = query.offset((page - 1) * limit).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "severity": log.severity,
                    "status": log.status,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat(),
                    "duration_ms": log.duration_ms
                }
                for log in logs
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения логов аудита: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения логов аудита"
        )


@router.get("/security-events")
async def get_security_events(
    page: int = 1,
    limit: int = 50,
    threat_level: Optional[str] = None,
    status: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получение событий безопасности"""
    try:
        query = db.query(SecurityEvent)
        
        # Фильтрация
        if threat_level:
            query = query.filter(SecurityEvent.threat_level == threat_level)
        if status:
            query = query.filter(SecurityEvent.status == status)
        
        # Сортировка по времени (новые сначала)
        query = query.order_by(SecurityEvent.created_at.desc())
        
        # Пагинация
        total = query.count()
        events = query.offset((page - 1) * limit).limit(limit).all()
        
        return {
            "events": [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "description": event.description,
                    "threat_level": event.threat_level,
                    "status": event.status,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "created_at": event.created_at.isoformat(),
                    "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
                    "resolved_by": event.resolved_by
                }
                for event in events
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения событий безопасности: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения событий безопасности"
        )


@router.get("/system/health")
async def get_system_health(
    current_admin: User = Depends(get_current_admin)
):
    """Получение состояния системы"""
    try:
        from ..services.unified_llm_service import unified_llm_service
        from ..services.embeddings_service import embeddings_service
        from ..services.vector_store_service import vector_store_service
        from ..services.rag_service import rag_service
        
        return {
            "ai_models": {
                "unified_llm_vistral_ready": unified_llm_service.is_model_loaded(),
                "embeddings_ready": embeddings_service.is_ready()
            },
            "vector_store": {
                "ready": vector_store_service.is_ready()
            },
            "rag_system": {
                "ready": rag_service.is_ready(),
                "status": rag_service.get_status()
            },
            "database": {
                "status": "connected"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения состояния системы: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения состояния системы"
        )
