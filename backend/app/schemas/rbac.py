"""
Pydantic схемы для RBAC (роли и права доступа)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PermissionBase(BaseModel):
    """Базовая схема права доступа"""
    name: str = Field(..., description="Название права (например, users.read)")
    display_name: str = Field(..., description="Человекочитаемое название")
    description: Optional[str] = Field(None, description="Описание права")
    resource: str = Field(..., description="Ресурс (например, users)")
    action: str = Field(..., description="Действие (например, read)")


class PermissionCreate(PermissionBase):
    """Схема для создания права доступа"""
    pass


class PermissionResponse(PermissionBase):
    """Схема ответа для права доступа"""
    id: int
    is_system: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Базовая схема роли"""
    name: str = Field(..., description="Название роли (например, admin)")
    display_name: str = Field(..., description="Человекочитаемое название")
    description: Optional[str] = Field(None, description="Описание роли")
    is_active: bool = Field(True, description="Активна ли роль")


class RoleCreate(RoleBase):
    """Схема для создания роли"""
    pass


class RoleUpdate(BaseModel):
    """Схема для обновления роли"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """Схема ответа для роли"""
    id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    """Схема для назначения роли пользователю"""
    role_id: int = Field(..., description="ID роли")
    reason: Optional[str] = Field(None, description="Причина назначения роли")


class UserRoleResponse(BaseModel):
    """Схема ответа для роли пользователя"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    assigned_at: datetime
    assigned_by: int
    
    class Config:
        from_attributes = True


class RolePermissionAssign(BaseModel):
    """Схема для назначения права роли"""
    permission_id: int = Field(..., description="ID права доступа")


class UserRoleHistoryResponse(BaseModel):
    """Схема ответа для истории ролей пользователя"""
    id: int
    user_id: int
    role_id: int
    action: str  # granted, revoked
    assigned_by: int
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SuperAdminProtectionResponse(BaseModel):
    """Схема ответа для защиты суперадмина"""
    is_protected: bool
    email: str
    last_login: Optional[datetime]
    two_factor_enabled: bool
    backup_codes_count: int
    emergency_token_active: bool
    emergency_token_expires: Optional[datetime]


class SuperAdminSafeguardsResponse(BaseModel):
    """Схема ответа для защитных механизмов суперадмина"""
    backup_codes: List[str]
    emergency_token: str
    instructions: dict


class EmergencyRecoveryRequest(BaseModel):
    """Схема запроса экстренного восстановления"""
    emergency_token: str = Field(..., description="Экстренный токен")
    new_password: str = Field(..., min_length=8, description="Новый пароль")


class RoleStatsResponse(BaseModel):
    """Схема ответа для статистики ролей"""
    total_roles: int
    active_roles: int
    system_roles: int
    custom_roles: int
    users_with_roles: int


class PermissionStatsResponse(BaseModel):
    """Схема ответа для статистики прав"""
    total_permissions: int
    system_permissions: int
    custom_permissions: int
    permissions_by_resource: dict


class RBACStatsResponse(BaseModel):
    """Схема ответа для общей статистики RBAC"""
    roles: RoleStatsResponse
    permissions: PermissionStatsResponse
    last_updated: datetime
