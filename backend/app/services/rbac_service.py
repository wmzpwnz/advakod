"""
Сервис для управления ролями и правами доступа (RBAC)
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import SessionLocal
from ..models.user import User
from ..models.rbac import (
    Role, Permission, UserRoleHistory, user_roles, role_permissions,
    SYSTEM_ROLES, SYSTEM_PERMISSIONS, ROLE_PERMISSIONS_MAPPING
)

logger = logging.getLogger(__name__)


class RBACService:
    """Сервис для управления ролями и правами"""
    
    def __init__(self):
        self.db = None
    
    def initialize_rbac_system(self, db: Session) -> bool:
        """Инициализация RBAC системы с предустановленными ролями и правами"""
        try:
            logger.info("🔧 Инициализация RBAC системы...")
            
            # 1. Создаем системные права
            self._create_system_permissions(db)
            
            # 2. Создаем системные роли
            self._create_system_roles(db)
            
            # 3. Назначаем права ролям
            self._assign_permissions_to_roles(db)
            
            # 4. Мигрируем существующих админов
            self._migrate_existing_admins(db)
            
            logger.info("✅ RBAC система инициализирована успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RBAC: {e}")
            return False
    
    def _create_system_permissions(self, db: Session):
        """Создает системные права"""
        for perm_name, perm_data in SYSTEM_PERMISSIONS.items():
            existing = db.query(Permission).filter(Permission.name == perm_name).first()
            if not existing:
                permission = Permission(
                    name=perm_name,
                    display_name=perm_data["display_name"],
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                    is_system=True
                )
                db.add(permission)
        
        db.commit()
        logger.info(f"✅ Создано {len(SYSTEM_PERMISSIONS)} системных прав")
    
    def _create_system_roles(self, db: Session):
        """Создает системные роли"""
        for role_name, role_data in SYSTEM_ROLES.items():
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                role = Role(
                    name=role_name,
                    display_name=role_data["display_name"],
                    description=role_data["description"],
                    is_system=role_data["is_system"],
                    is_active=True
                )
                db.add(role)
        
        db.commit()
        logger.info(f"✅ Создано {len(SYSTEM_ROLES)} системных ролей")
    
    def _assign_permissions_to_roles(self, db: Session):
        """Назначает права ролям"""
        for role_name, permission_names in ROLE_PERMISSIONS_MAPPING.items():
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                continue
            
            for perm_name in permission_names:
                permission = db.query(Permission).filter(Permission.name == perm_name).first()
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)
        
        db.commit()
        logger.info("✅ Права назначены ролям")
    
    def _migrate_existing_admins(self, db: Session):
        """Мигрирует существующих админов в RBAC систему"""
        # Находим всех существующих админов
        existing_admins = db.query(User).filter(User.is_admin == True).all()
        
        # Получаем роль super_admin
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        
        if not super_admin_role:
            logger.error("❌ Роль super_admin не найдена")
            return
        
        for admin in existing_admins:
            # Проверяем, есть ли уже роли у админа
            if not admin.get_roles():
                # Назначаем роль super_admin
                self.assign_role_to_user(db, admin.id, super_admin_role.id, assigned_by=admin.id)
                logger.info(f"✅ Роль super_admin назначена пользователю {admin.email}")
    
    def assign_role_to_user(self, db: Session, user_id: int, role_id: int, assigned_by: int, reason: str = None) -> bool:
        """Назначает роль пользователю"""
        try:
            # Проверяем, что роль еще не назначена
            existing = db.execute(
                user_roles.select().where(
                    and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role_id)
                )
            ).first()
            
            if existing:
                return False  # Роль уже назначена
            
            # Назначаем роль
            db.execute(
                user_roles.insert().values(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by
                )
            )
            
            # Записываем в историю
            history = UserRoleHistory(
                user_id=user_id,
                role_id=role_id,
                action="granted",
                assigned_by=assigned_by,
                reason=reason
            )
            db.add(history)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка назначения роли: {e}")
            db.rollback()
            return False
    
    def revoke_role_from_user(self, db: Session, user_id: int, role_id: int, revoked_by: int, reason: str = None) -> bool:
        """Отзывает роль у пользователя"""
        try:
            # Удаляем назначение роли
            result = db.execute(
                user_roles.delete().where(
                    and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role_id)
                )
            )
            
            if result.rowcount == 0:
                return False  # Роль не была назначена
            
            # Записываем в историю
            history = UserRoleHistory(
                user_id=user_id,
                role_id=role_id,
                action="revoked",
                assigned_by=revoked_by,
                reason=reason
            )
            db.add(history)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отзыва роли: {e}")
            db.rollback()
            return False
    
    def check_permission(self, user: User, permission_name: str) -> bool:
        """Проверяет, есть ли у пользователя определенное право"""
        return user.has_permission(permission_name)
    
    def get_user_roles(self, db: Session, user_id: int) -> List[Role]:
        """Получает все роли пользователя"""
        return db.query(Role).join(user_roles).filter(user_roles.c.user_id == user_id).all()
    
    def get_role_permissions(self, db: Session, role_id: int) -> List[Permission]:
        """Получает все права роли"""
        return db.query(Permission).join(role_permissions).filter(role_permissions.c.role_id == role_id).all()
    
    def get_all_roles(self, db: Session, include_inactive: bool = False) -> List[Role]:
        """Получает все роли в системе"""
        query = db.query(Role)
        if not include_inactive:
            query = query.filter(Role.is_active == True)
        return query.order_by(Role.name).all()
    
    def get_all_permissions(self, db: Session) -> List[Permission]:
        """Получает все права в системе"""
        return db.query(Permission).order_by(Permission.resource, Permission.action).all()
    
    def get_role_by_name(self, db: Session, role_name: str) -> Optional[Role]:
        """Получает роль по имени"""
        return db.query(Role).filter(Role.name == role_name).first()
    
    def create_custom_role(self, db: Session, name: str, display_name: str, description: str = None, created_by: int = None) -> Role:
        """Создает пользовательскую роль"""
        try:
            role = Role(
                name=name,
                display_name=display_name,
                description=description,
                is_system=False,
                is_active=True
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            
            logger.info(f"✅ Создана пользовательская роль: {name}")
            return role
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания роли: {e}")
            db.rollback()
            raise
    
    def get_user_role_history(self, db: Session, user_id: int) -> List[UserRoleHistory]:
        """Получает историю изменений ролей пользователя"""
        return db.query(UserRoleHistory).filter(
            UserRoleHistory.user_id == user_id
        ).order_by(UserRoleHistory.created_at.desc()).all()


# Глобальный экземпляр сервиса
rbac_service = RBACService()


def require_permission(permission_name: str):
    """Декоратор для проверки прав доступа"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем пользователя в аргументах
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if not current_user:
                # Ищем в kwargs
                current_user = kwargs.get('current_admin') or kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="Пользователь не найден")
            
            # Проверяем право
            if not current_user.has_permission(permission_name):
                logger.warning(f"🚫 Пользователь {current_user.email} попытался выполнить действие без права {permission_name}")
                raise HTTPException(
                    status_code=403, 
                    detail=f"Недостаточно прав. Требуется: {permission_name}"
                )
            
            import asyncio
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator
