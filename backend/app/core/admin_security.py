"""
Дополнительные меры безопасности для админки
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
import ipaddress

from .database import get_db
from .config import settings
from ..models.user import User
from ..models.audit_log import AuditLog, ActionType, SeverityLevel
from ..services.auth_service import auth_service

logger = logging.getLogger(__name__)


class AdminSecurityService:
    """Сервис безопасности для админки"""
    
    def __init__(self):
        # Белый список IP адресов для админов (можно настроить через .env)
        self.admin_ip_whitelist = self._load_ip_whitelist()
        # Максимальное количество попыток входа
        self.max_login_attempts = 3
        # Блокировка на 15 минут после превышения попыток
        self.lockout_duration = timedelta(minutes=15)
        # Кэш неудачных попыток {ip: [timestamp1, timestamp2, ...]}
        self.failed_attempts = {}
        
    def _load_ip_whitelist(self) -> list:
        """Загружает белый список IP адресов"""
        whitelist_str = settings.ADMIN_IP_WHITELIST
        
        whitelist = []
        for ip_str in whitelist_str.split(","):
            ip_str = ip_str.strip()
            if ip_str:
                try:
                    # Проверяем, что это валидный IP
                    if ip_str == "localhost":
                        whitelist.extend(["127.0.0.1", "::1"])
                    else:
                        ipaddress.ip_address(ip_str)
                        whitelist.append(ip_str)
                except ValueError:
                    logger.warning(f"⚠️ Некорректный IP в whitelist: {ip_str}")
        
        logger.info(f"🔒 Admin IP whitelist: {whitelist}")
        return whitelist
    
    def check_admin_ip_access(self, request: Request) -> bool:
        """Проверяет, разрешен ли доступ с данного IP"""
        # В разработке пропускаем проверку IP
        import os
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.info("🔓 В режиме разработки - пропускаем проверку IP")
            return True
            
        # Если whitelist пустой, пропускаем проверку (для удобства настройки)
        if not self.admin_ip_whitelist:
            logger.info("🔓 IP whitelist пуст - пропускаем проверку IP")
            return True
            
        client_ip = self.get_client_ip(request)
        
        # Проверяем whitelist
        if client_ip not in self.admin_ip_whitelist:
            logger.warning(f"🚫 Попытка доступа к админке с неразрешенного IP: {client_ip}")
            return False
            
        return True
    
    def get_client_ip(self, request: Request) -> str:
        """Получает реальный IP клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    def check_admin_brute_force(self, request: Request) -> bool:
        """Проверяет на brute force атаки"""
        client_ip = self.get_client_ip(request)
        current_time = datetime.utcnow()
        
        # Очищаем старые попытки
        if client_ip in self.failed_attempts:
            self.failed_attempts[client_ip] = [
                attempt_time for attempt_time in self.failed_attempts[client_ip]
                if current_time - attempt_time < self.lockout_duration
            ]
        
        # Проверяем количество попыток
        attempts_count = len(self.failed_attempts.get(client_ip, []))
        
        if attempts_count >= self.max_login_attempts:
            logger.warning(f"🚫 IP {client_ip} заблокирован за превышение попыток входа в админку")
            return False
            
        return True
    
    def record_failed_admin_login(self, request: Request):
        """Записывает неудачную попытку входа в админку"""
        client_ip = self.get_client_ip(request)
        current_time = datetime.utcnow()
        
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
            
        self.failed_attempts[client_ip].append(current_time)
        
        attempts_count = len(self.failed_attempts[client_ip])
        logger.warning(f"⚠️ Неудачная попытка входа в админку с IP {client_ip}. Попытка {attempts_count}/{self.max_login_attempts}")
    
    def validate_admin_action(self, user: User, action: str, resource: str = None) -> bool:
        """Валидирует админское действие"""
        
        # Базовые проверки
        if not user.is_admin:
            return False
            
        if not user.is_active:
            return False
        
        # Проверяем критические действия
        critical_actions = [
            "delete_user",
            "toggle_admin_status", 
            "clear_all_documents",
            "delete_document",
            "modify_system_settings"
        ]
        
        if action in critical_actions:
            # Для критических действий требуем дополнительные проверки
            logger.warning(f"🔥 Критическое админское действие: {action} от пользователя {user.email}")
            
            # Можно добавить дополнительные проверки:
            # - Требовать повторную аутентификацию
            # - Проверять 2FA
            # - Логировать в отдельный файл
            
        return True


# Глобальный экземпляр
admin_security = AdminSecurityService()


def get_secure_admin(
    request: Request,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """Усиленная проверка прав администратора с дополнительными мерами безопасности"""
    
    # 1. Базовая проверка админских прав
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    
    # 2. Проверка IP whitelist (в продакшене)
    if not admin_security.check_admin_ip_access(request):
        # Логируем подозрительную активность
        audit_log = AuditLog(
            user_id=current_user.id,
            action=ActionType.SECURITY_INCIDENT,
            resource="admin_access",
            description=f"Попытка доступа к админке с неразрешенного IP: {admin_security._get_client_ip(request)}",
            severity=SeverityLevel.HIGH,
            ip_address=admin_security._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            status="blocked"
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(
            status_code=403, 
            detail="Доступ к админке разрешен только с авторизованных IP адресов"
        )
    
    # 3. Проверка активности аккаунта
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт администратора деактивирован")
    
    # 4. Логируем админский доступ
    audit_log = AuditLog(
        user_id=current_user.id,
        action=ActionType.ADMIN_ACCESS,
        resource="admin_panel",
        description=f"Доступ к админ панели",
        severity=SeverityLevel.MEDIUM,
        ip_address=admin_security._get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        status="success"
    )
    db.add(audit_log)
    db.commit()
    
    return current_user


def require_admin_action_validation(action: str, resource: str = None):
    """Декоратор для валидации критических админских действий"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Получаем пользователя из аргументов
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if not current_user:
                # Ищем в kwargs
                current_user = kwargs.get('current_admin') or kwargs.get('current_user')
            
            if current_user and not admin_security.validate_admin_action(current_user, action, resource):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Недостаточно прав для выполнения действия: {action}"
                )
            
            import asyncio
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator
