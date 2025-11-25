"""
Система разрешений для админ-панели
"""
from functools import wraps
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from ..models.user import User
from ..services.auth_service import AuthService

auth_service = AuthService()

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Определение разрешений для различных ролей
ROLE_PERMISSIONS = {
    "super_admin": [
        "view_all_data",
        "manage_users",
        "manage_system",
        "view_system_stats",
        "send_admin_broadcasts",
        "send_admin_notifications",
        "manage_backups",
        "manage_roles",
        "view_security_logs",
        "manage_settings"
    ],
    "admin": [
        "view_dashboard",
        "manage_users",
        "view_analytics",
        "send_admin_notifications",
        "view_system_stats",
        "manage_moderation"
    ],
    "moderator": [
        "view_dashboard",
        "manage_moderation",
        "view_user_reports",
        "moderate_content"
    ],
    "analyst": [
        "view_dashboard",
        "view_analytics",
        "view_user_activity",
        "view_performance_metrics",
        "export_reports"
    ],
    "marketing_manager": [
        "view_dashboard",
        "view_marketing_analytics",
        "manage_campaigns",
        "view_conversion_tracking",
        "manage_promotions"
    ],
    "project_manager": [
        "view_dashboard",
        "manage_projects",
        "view_task_management",
        "view_resource_tracking",
        "manage_team"
    ]
}


def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя-администратора"""
    try:
        payload = auth_service.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or insufficient permissions"
        )


def has_permission(user: User, permission: str) -> bool:
    """Проверка наличия разрешения у пользователя"""
    if not user.is_admin:
        return False
    
    user_role = getattr(user, 'role', 'admin')  # Используем 'admin' как значение по умолчанию
    role_permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    # super_admin имеет все разрешения
    if user_role == "super_admin":
        return True
    
    return permission in role_permissions


def require_permission(permission: str):
    """Декоратор для проверки разрешений"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем пользователя из kwargs (должен быть передан как current_user)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin_permission(permission: str):
    """Dependency для проверки админских разрешений"""
    def check_permission(current_user: User = Depends(get_current_admin_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return check_permission


def require_any_admin_role():
    """Dependency для проверки любой админской роли"""
    def check_admin_role(current_user: User = Depends(get_current_admin_user)) -> User:
        return current_user
    
    return check_admin_role


def require_specific_role(required_role: str):
    """Dependency для проверки конкретной роли"""
    def check_role(current_user: User = Depends(get_current_admin_user)) -> User:
        user_role = getattr(current_user, 'role', 'admin')
        if user_role != required_role and user_role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return check_role


def get_user_permissions(user: User) -> List[str]:
    """Получение списка разрешений пользователя"""
    if not user.is_admin:
        return []
    
    user_role = getattr(user, 'role', 'admin')
    return ROLE_PERMISSIONS.get(user_role, [])


def can_access_module(user: User, module: str) -> bool:
    """Проверка доступа к модулю админ-панели"""
    module_permissions = {
        "dashboard": ["view_dashboard"],
        "users": ["manage_users"],
        "analytics": ["view_analytics"],
        "moderation": ["manage_moderation"],
        "marketing": ["view_marketing_analytics"],
        "projects": ["manage_projects"],
        "system": ["manage_system"],
        "backups": ["manage_backups"],
        "settings": ["manage_settings"]
    }
    
    required_permissions = module_permissions.get(module, [])
    return any(has_permission(user, perm) for perm in required_permissions)