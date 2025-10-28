from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)  # Индекс для фильтрации активных пользователей
    is_premium = Column(Boolean, default=False, index=True)  # Индекс для фильтрации премиум пользователей
    is_admin = Column(Boolean, default=False, index=True)  # Администратор системы + индекс
    subscription_type = Column(String(50), default="free")  # free, basic, premium
    subscription_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительные поля для ИИ-юриста
    company_name = Column(String(255), nullable=True)
    legal_form = Column(String(100), nullable=True)  # ИП, ООО, АО и т.д.
    inn = Column(String(12), nullable=True)
    ogrn = Column(String(15), nullable=True)
    
    # 2FA поля
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32), nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON строка с резервными кодами
    
    # Связи (временно отключены для исправления ошибки 500)
    # Все relationships закомментированы до полной настройки моделей
    pass

    
    # RBAC связь (будет определена после импорта rbac модулей)
    # roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # RBAC связи (импортируем после определения таблиц)
    def get_roles(self):
        """Получает роли пользователя (временно отключено)"""
        # Временно возвращаем пустой список до настройки RBAC
        return []
    
    def has_permission(self, permission_name: str) -> bool:
        """Проверяет, есть ли у пользователя определенное право (временно упрощено)"""
        if self.is_admin:
            # Обратная совместимость: старые админы имеют все права
            return True
        # Временно возвращаем False для обычных пользователей
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Проверяет, есть ли у пользователя определенная роль (временно упрощено)"""
        # Временно возвращаем False до настройки RBAC
        return False
    
    def get_permissions(self) -> list:
        """Получает все права пользователя (временно упрощено)"""
        # Временно возвращаем пустой список до настройки RBAC
        return []
