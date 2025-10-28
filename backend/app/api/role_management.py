"""
API для управления ролями и правами доступа
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..models.rbac import Role, Permission, UserRoleHistory, user_roles, role_permissions
from ..schemas.rbac import (
    RoleCreate, RoleUpdate, RoleResponse, PermissionResponse,
    UserRoleAssign, UserRoleResponse, RolePermissionAssign
)
from ..services.auth_service import AuthService
from ..services.rbac_service import rbac_service, require_permission
from ..core.superadmin_protection import superadmin_protection, require_superadmin_protection
from ..core.admin_security import get_secure_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/roles", tags=["role-management"])
auth_service = AuthService()


def get_current_admin(current_user: User = Depends(auth_service.get_current_user)) -> User:
    """Получение текущего администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора"
        )
    return current_user


# ==================== УПРАВЛЕНИЕ РОЛЯМИ ====================

@router.get("/", response_model=List[RoleResponse])
@require_permission("roles.read")
async def get_roles(
    include_inactive: bool = False,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список всех ролей"""
    try:
        roles = rbac_service.get_all_roles(db, include_inactive)
        return [RoleResponse.from_orm(role) for role in roles]
    except Exception as e:
        logger.error(f"Ошибка получения ролей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_id}", response_model=RoleResponse)
@require_permission("roles.read")
async def get_role(
    role_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить роль по ID"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        return RoleResponse.from_orm(role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения роли {role_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=RoleResponse)
@require_permission("roles.write")
async def create_role(
    role_data: RoleCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Создать новую роль"""
    try:
        # Проверяем, что роль с таким именем не существует
        existing_role = db.query(Role).filter(Role.name == role_data.name).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
        
        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            is_system=False,
            is_active=True
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        logger.info(f"Создана новая роль: {role.name} (ID: {role.id})")
        return RoleResponse.from_orm(role)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания роли: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{role_id}", response_model=RoleResponse)
@require_permission("roles.write")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Обновить роль"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Нельзя изменять системные роли
        if role.is_system:
            raise HTTPException(status_code=400, detail="Нельзя изменять системные роли")
        
        # Обновляем поля
        if role_data.display_name is not None:
            role.display_name = role_data.display_name
        if role_data.description is not None:
            role.description = role_data.description
        if role_data.is_active is not None:
            role.is_active = role_data.is_active
        
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        
        logger.info(f"Обновлена роль: {role.name} (ID: {role.id})")
        return RoleResponse.from_orm(role)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления роли {role_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{role_id}")
@require_permission("roles.write")
async def delete_role(
    role_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Удалить роль"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Нельзя удалять системные роли
        if role.is_system:
            raise HTTPException(status_code=400, detail="Нельзя удалять системные роли")
        
        # Проверяем, используется ли роль
        users_with_role = db.execute(
            user_roles.select().where(user_roles.c.role_id == role_id)
        ).fetchall()
        
        if users_with_role:
            raise HTTPException(
                status_code=400, 
                detail=f"Роль используется {len(users_with_role)} пользователями. Сначала отзовите роль у всех пользователей."
            )
        
        db.delete(role)
        db.commit()
        
        logger.info(f"Удалена роль: {role.name} (ID: {role_id})")
        return {"message": "Роль успешно удалена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления роли {role_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УПРАВЛЕНИЕ ПРАВАМИ ====================

@router.get("/permissions/", response_model=List[PermissionResponse])
@require_permission("roles.read")
async def get_permissions(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список всех прав"""
    try:
        permissions = rbac_service.get_all_permissions(db)
        return [PermissionResponse.from_orm(perm) for perm in permissions]
    except Exception as e:
        logger.error(f"Ошибка получения прав: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_id}/permissions/", response_model=List[PermissionResponse])
@require_permission("roles.read")
async def get_role_permissions(
    role_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить права роли"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        permissions = rbac_service.get_role_permissions(db, role_id)
        return [PermissionResponse.from_orm(perm) for perm in permissions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения прав роли {role_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{role_id}/permissions/")
@require_permission("roles.write")
async def assign_permission_to_role(
    role_id: int,
    permission_data: RolePermissionAssign,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Назначить право роли"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        permission = db.query(Permission).filter(Permission.id == permission_data.permission_id).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Право не найдено")
        
        # Проверяем, не назначено ли уже
        existing = db.execute(
            role_permissions.select().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_data.permission_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Право уже назначено роли")
        
        # Назначаем право
        db.execute(
            role_permissions.insert().values(
                role_id=role_id,
                permission_id=permission_data.permission_id
            )
        )
        db.commit()
        
        logger.info(f"Назначено право {permission.name} роли {role.name}")
        return {"message": "Право успешно назначено роли"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка назначения права роли: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{role_id}/permissions/{permission_id}")
@require_permission("roles.write")
async def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Отозвать право у роли"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Нельзя отзывать права у системных ролей
        if role.is_system:
            raise HTTPException(status_code=400, detail="Нельзя изменять права системных ролей")
        
        result = db.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id
            )
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Право не назначено роли")
        
        db.commit()
        
        logger.info(f"Отозвано право {permission_id} у роли {role.name}")
        return {"message": "Право успешно отозвано у роли"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отзыва права у роли: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УПРАВЛЕНИЕ РОЛЯМИ ПОЛЬЗОВАТЕЛЕЙ ====================

@router.get("/users/{user_id}/roles/", response_model=List[UserRoleResponse])
@require_permission("roles.read")
async def get_user_roles(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить роли пользователя"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        roles = rbac_service.get_user_roles(db, user_id)
        return [UserRoleResponse.from_orm(role) for role in roles]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения ролей пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/roles/")
@require_permission("roles.assign")
async def assign_role_to_user(
    user_id: int,
    role_data: UserRoleAssign,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Назначить роль пользователю"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        role = db.query(Role).filter(Role.id == role_data.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Проверяем права на назначение роли
        if role.name == "super_admin" and not superadmin_protection.is_superadmin(current_admin):
            raise HTTPException(
                status_code=403, 
                detail="Только суперадмин может назначать роль super_admin"
            )
        
        success = rbac_service.assign_role_to_user(
            db, user_id, role_data.role_id, current_admin.id, role_data.reason
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Роль уже назначена пользователю")
        
        logger.info(f"Назначена роль {role.name} пользователю {user.email}")
        return {"message": "Роль успешно назначена пользователю"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка назначения роли пользователю: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/roles/{role_id}")
@require_permission("roles.assign")
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    reason: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Отозвать роль у пользователя"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Нельзя отзывать роль super_admin у суперадмина
        if role.name == "super_admin" and superadmin_protection.is_superadmin(user):
            raise HTTPException(
                status_code=400, 
                detail="Нельзя отзывать роль super_admin у суперадмина"
            )
        
        success = rbac_service.revoke_role_from_user(
            db, user_id, role_id, current_admin.id, reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Роль не назначена пользователю")
        
        logger.info(f"Отозвана роль {role.name} у пользователя {user.email}")
        return {"message": "Роль успешно отозвана у пользователя"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отзыва роли у пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ЗАЩИТА СУПЕРАДМИНА ====================

@router.get("/superadmin/protection/")
@require_superadmin_protection()
async def get_superadmin_protection(
    current_admin: User = Depends(get_current_admin)
):
    """Получить статус защиты суперадмина"""
    try:
        protection_status = superadmin_protection.protect_superadmin_account(current_admin)
        return protection_status
    except Exception as e:
        logger.error(f"Ошибка получения статуса защиты: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/superadmin/safeguards/")
@require_superadmin_protection()
async def create_superadmin_safeguards(
    current_admin: User = Depends(get_current_admin)
):
    """Создать защитные механизмы для суперадмина"""
    try:
        safeguards = superadmin_protection.create_superadmin_safeguards()
        return safeguards
    except Exception as e:
        logger.error(f"Ошибка создания защитных механизмов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/superadmin/emergency-recovery/")
async def emergency_access_recovery(
    emergency_token: str,
    new_password: str
):
    """Экстренное восстановление доступа суперадмина"""
    try:
        success = superadmin_protection.emergency_access_recovery(emergency_token, new_password)
        if success:
            return {"message": "Доступ успешно восстановлен"}
        else:
            raise HTTPException(status_code=400, detail="Неверный токен или истек срок действия")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экстренного восстановления: {e}")
        raise HTTPException(status_code=500, detail=str(e))
