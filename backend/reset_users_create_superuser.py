#!/usr/bin/env python3
"""
Script to reset all users and create a single superuser
DANGER: This will delete ALL existing users and create only one superuser
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.services.auth_service import AuthService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_and_create_superuser():
    """Delete all users and create a single superuser"""
    db = SessionLocal()
    auth_service = AuthService()
    
    # Superuser credentials
    SUPERUSER_EMAIL = "aziz@bagbekov.ru"
    SUPERUSER_PASSWORD = "Davidiseen13$$13"
    SUPERUSER_USERNAME = "aziz_admin"
    SUPERUSER_FULL_NAME = "Aziz Bagbekov (Superuser)"
    
    try:
        logger.warning("🚨 DANGER: This will DELETE ALL existing users!")
        logger.info("Proceeding with user reset...")
        
        # Step 1: Count existing users
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        regular_users = total_users - admin_users
        
        logger.info(f"Found {total_users} total users:")
        logger.info(f"  - {admin_users} admin users")
        logger.info(f"  - {regular_users} regular users")
        
        # Step 2: Delete all existing users
        if total_users > 0:
            deleted_count = db.query(User).delete()
            logger.warning(f"🗑️  Deleted {deleted_count} users")
        else:
            logger.info("No existing users to delete")
        
        # Step 3: Create the new superuser
        logger.info("🔧 Creating new superuser...")
        
        # Hash the password
        hashed_password = auth_service.get_password_hash(SUPERUSER_PASSWORD)
        
        # Create superuser
        superuser = User(
            username=SUPERUSER_USERNAME,
            email=SUPERUSER_EMAIL,
            hashed_password=hashed_password,
            full_name=SUPERUSER_FULL_NAME,
            is_admin=True,
            is_active=True,
            is_premium=True,
            subscription_type="premium",
            two_factor_enabled=False  # Can be enabled later
        )
        
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        
        logger.info("✅ Superuser created successfully!")
        logger.info("=" * 50)
        logger.info("📋 SUPERUSER CREDENTIALS:")
        logger.info(f"   Email: {superuser.email}")
        logger.info(f"   Username: {superuser.username}")
        logger.info(f"   Password: {SUPERUSER_PASSWORD}")
        logger.info(f"   Full Name: {superuser.full_name}")
        logger.info(f"   User ID: {superuser.id}")
        logger.info(f"   Admin: {superuser.is_admin}")
        logger.info(f"   Active: {superuser.is_active}")
        logger.info(f"   Premium: {superuser.is_premium}")
        logger.info("=" * 50)
        logger.warning("🔒 IMPORTANT: Save these credentials securely!")
        logger.info("🌐 You can now login to the admin panel with these credentials")
        logger.info("🔗 Admin login URL: https://advacodex.com/admin-login")
        
        # Verify the user can authenticate
        test_auth = auth_service.authenticate_user(db, SUPERUSER_EMAIL, SUPERUSER_PASSWORD)
        if test_auth:
            logger.info("✅ Authentication test PASSED")
        else:
            logger.error("❌ Authentication test FAILED - something went wrong!")
            
    except Exception as e:
        logger.error(f"❌ Error during user reset: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def verify_database_connection():
    """Verify database connection before proceeding"""
    try:
        db = SessionLocal()
        # Test connection
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Database connection verified")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting user reset and superuser creation...")
    
    # Verify database connection
    if not verify_database_connection():
        logger.error("Cannot proceed without database connection")
        sys.exit(1)
    
    # Final confirmation
    logger.warning("⚠️  WARNING: This will permanently delete ALL users!")
    logger.info("Proceeding in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        reset_and_create_superuser()
        logger.info("🎉 User reset completed successfully!")
        logger.info("You can now access the admin panel with the new superuser credentials")
    except Exception as e:
        logger.error(f"💥 Failed to complete user reset: {e}")
        sys.exit(1)