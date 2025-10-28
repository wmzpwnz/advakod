"""
Модели для Role-Based Access Control (RBAC)
Система ролей и прав доступа
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


# Таблица связи many-to-many между пользователями и ролями
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id'), nullable=True)  # Кто назначил роль
)

# Таблица связи many-to-many между ролями и правами
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now())
)


class Role(Base):
    """Роли в системе"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # super_admin, admin, moderator, etc.
    display_name = Column(String(100), nullable=False)  # Человекочитаемое название
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)  # Системная роль (нельзя удалить)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи (убираем back_populates для избежания циклических зависимостей)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, display_name={self.display_name})>"


class Permission(Base):
    """Права доступа в системе"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # users.read, users.write, etc.
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False, index=True)  # users, documents, system, etc.
    action = Column(String(50), nullable=False, index=True)    # read, write, delete, etc.
    is_system = Column(Boolean, default=False)  # Системное право (нельзя удалить)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"


class UserRoleHistory(Base):
    """История изменений ролей пользователей"""
    __tablename__ = "user_role_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    action = Column(String(20), nullable=False)  # granted, revoked
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Кто изменил
    reason = Column(Text, nullable=True)  # Причина изменения
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRoleHistory(user_id={self.user_id}, role_id={self.role_id}, action={self.action})>"


# Предустановленные роли системы
SYSTEM_ROLES = {
    "super_admin": {
        "display_name": "Супер-администратор",
        "description": "Полный доступ ко всем функциям системы",
        "is_system": True
    },
    "admin": {
        "display_name": "Администратор",
        "description": "Управление пользователями и контентом",
        "is_system": True
    },
    "moderator": {
        "display_name": "Модератор",
        "description": "Модерация контента и пользователей",
        "is_system": True
    },
    "content_manager": {
        "display_name": "Контент-менеджер", 
        "description": "Управление документами и базой знаний",
        "is_system": True
    },
    "support": {
        "display_name": "Поддержка",
        "description": "Техническая поддержка пользователей",
        "is_system": True
    },
    "analyst": {
        "display_name": "Аналитик",
        "description": "Просмотр аналитики и отчетов",
        "is_system": True
    }
}

# Предустановленные права доступа
SYSTEM_PERMISSIONS = {
    # Управление пользователями
    "users.read": {"display_name": "Просмотр пользователей", "resource": "users", "action": "read"},
    "users.write": {"display_name": "Редактирование пользователей", "resource": "users", "action": "write"},
    "users.delete": {"display_name": "Удаление пользователей", "resource": "users", "action": "delete"},
    "users.admin": {"display_name": "Управление админами", "resource": "users", "action": "admin"},
    
    # Управление документами
    "documents.read": {"display_name": "Просмотр документов", "resource": "documents", "action": "read"},
    "documents.write": {"display_name": "Загрузка документов", "resource": "documents", "action": "write"},
    "documents.delete": {"display_name": "Удаление документов", "resource": "documents", "action": "delete"},
    "documents.validate": {"display_name": "Валидация документов", "resource": "documents", "action": "validate"},
    
    # Управление чатами
    "chats.read": {"display_name": "Просмотр чатов", "resource": "chats", "action": "read"},
    "chats.delete": {"display_name": "Удаление чатов", "resource": "chats", "action": "delete"},
    "chats.moderate": {"display_name": "Модерация чатов", "resource": "chats", "action": "moderate"},
    
    # Системные права
    "system.settings": {"display_name": "Настройки системы", "resource": "system", "action": "settings"},
    "system.monitoring": {"display_name": "Мониторинг системы", "resource": "system", "action": "monitoring"},
    "system.backup": {"display_name": "Резервное копирование", "resource": "system", "action": "backup"},
    "system.logs": {"display_name": "Просмотр логов", "resource": "system", "action": "logs"},
    
    # Управление ролями
    "roles.read": {"display_name": "Просмотр ролей", "resource": "roles", "action": "read"},
    "roles.write": {"display_name": "Управление ролями", "resource": "roles", "action": "write"},
    "roles.assign": {"display_name": "Назначение ролей", "resource": "roles", "action": "assign"},
    
    # Аналитика
    "analytics.read": {"display_name": "Просмотр аналитики", "resource": "analytics", "action": "read"},
    "analytics.export": {"display_name": "Экспорт данных", "resource": "analytics", "action": "export"},
}

# Предустановленные назначения ролей
ROLE_PERMISSIONS_MAPPING = {
    "super_admin": [
        # Супер-админ имеет ВСЕ права
        "users.read", "users.write", "users.delete", "users.admin",
        "documents.read", "documents.write", "documents.delete", "documents.validate",
        "chats.read", "chats.delete", "chats.moderate",
        "system.settings", "system.monitoring", "system.backup", "system.logs",
        "roles.read", "roles.write", "roles.assign",
        "analytics.read", "analytics.export"
    ],
    "admin": [
        # Обычный админ - без системных настроек и управления ролями
        "users.read", "users.write", "users.delete",
        "documents.read", "documents.write", "documents.delete", "documents.validate",
        "chats.read", "chats.delete", "chats.moderate",
        "system.monitoring", "system.logs",
        "analytics.read"
    ],
    "moderator": [
        # Модератор - управление контентом и пользователями
        "users.read", "users.write",
        "documents.read", "documents.write", "documents.validate",
        "chats.read", "chats.moderate",
        "analytics.read"
    ],
    "content_manager": [
        # Контент-менеджер - только документы
        "documents.read", "documents.write", "documents.delete", "documents.validate",
        "analytics.read"
    ],
    "support": [
        # Поддержка - просмотр пользователей и чатов
        "users.read",
        "chats.read",
        "system.logs"
    ],
    "analyst": [
        # Аналитик - только аналитика
        "analytics.read", "analytics.export",
        "users.read",
        "chats.read"
    ]
}
