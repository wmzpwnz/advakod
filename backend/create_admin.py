#!/usr/bin/env python3
"""
Скрипт для создания первого администратора с повышенной безопасностью
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.secure_auth import create_secure_admin_user, secure_password_manager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin():
    """Создает первого администратора с безопасным паролем"""
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # Проверяем, есть ли уже администраторы
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            logger.error(f"Администратор уже существует: {existing_admin.username} ({existing_admin.email})")
            return
        
        logger.info("🔧 Создание первого администратора с повышенной безопасностью...")
        
        # Создаем безопасного администратора
        admin_data = create_secure_admin_user()
        
        # Проверяем, существует ли пользователь с таким email
        existing_user = db.query(User).filter(User.email == admin_data["email"]).first()
        if existing_user:
            logger.error(f"Пользователь с email {admin_data['email']} уже существует")
            return
        
        # Проверяем, существует ли пользователь с таким username
        existing_username = db.query(User).filter(User.username == admin_data["username"]).first()
        if existing_username:
            logger.error(f"Пользователь с username {admin_data['username']} уже существует")
            return
        
        # Создаем администратора с безопасным хешированием
        admin_user = User(
            username=admin_data["username"],
            email=admin_data["email"],
            hashed_password=admin_data["password_hash"],
            full_name=admin_data["full_name"],
            is_admin=admin_data["is_admin"],
            is_premium=admin_data["is_premium"],
            is_active=admin_data["is_active"],
            subscription_type=admin_data["subscription_type"]
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("✅ Администратор создан успешно!")
        logger.info(f"   Username: {admin_user.username}")
        logger.info(f"   Email: {admin_user.email}")
        logger.info(f"   Password: {admin_data['password']}")
        logger.info(f"   ID: {admin_user.id}")
        logger.info(f"   Security Level: HIGH")
        logger.warning("🔒 ВАЖНО: Сохраните пароль в безопасном месте!")
        logger.info("🔒 Пароль сгенерирован с использованием криптографически стойкого алгоритма")
        logger.info("🔒 Рекомендуется сменить пароль после первого входа")
        
    except Exception as e:
        logger.error(f"Ошибка создания администратора: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
