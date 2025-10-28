#!/usr/bin/env python3
"""
Simple script to reset users and create superuser
Using minimal dependencies - direct SQLite approach
"""

import sqlite3
import hashlib
import secrets
import bcrypt
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def reset_and_create_superuser():
    """Reset users and create superuser using direct SQLite access"""
    
    # Database path
    db_path = "/Users/macbook/Desktop/advakod/backend/ai_lawyer.db"
    
    # Superuser credentials
    SUPERUSER_EMAIL = "aziz@bagbekov.ru"
    SUPERUSER_PASSWORD = "Davidiseen13$$13"
    SUPERUSER_USERNAME = "aziz_admin"
    SUPERUSER_FULL_NAME = "Aziz Bagbekov (Superuser)"
    
    print("🚀 Starting user reset and superuser creation...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ Users table not found in database")
            return
        
        # Count existing users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_users = cursor.fetchone()[0]
        
        print(f"📊 Found {total_users} total users ({admin_users} admin users)")
        
        # Delete all existing users
        if total_users > 0:
            cursor.execute("DELETE FROM users")
            print(f"🗑️  Deleted {total_users} users")
        
        # Hash the password
        hashed_password = hash_password(SUPERUSER_PASSWORD)
        
        # Create timestamp
        now = datetime.now().isoformat()
        
        # Insert new superuser
        cursor.execute("""
            INSERT INTO users (
                email, username, hashed_password, full_name, 
                is_active, is_premium, is_admin, subscription_type,
                created_at, updated_at, two_factor_enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            SUPERUSER_EMAIL,
            SUPERUSER_USERNAME, 
            hashed_password,
            SUPERUSER_FULL_NAME,
            1,  # is_active
            1,  # is_premium  
            1,  # is_admin
            "premium",  # subscription_type
            now,  # created_at
            now,  # updated_at
            0   # two_factor_enabled
        ))
        
        # Get the new user ID
        user_id = cursor.lastrowid
        
        # Commit changes
        conn.commit()
        
        print("✅ Superuser created successfully!")
        print("=" * 50)
        print("📋 SUPERUSER CREDENTIALS:")
        print(f"   Email: {SUPERUSER_EMAIL}")
        print(f"   Username: {SUPERUSER_USERNAME}")
        print(f"   Password: {SUPERUSER_PASSWORD}")
        print(f"   Full Name: {SUPERUSER_FULL_NAME}")
        print(f"   User ID: {user_id}")
        print(f"   Admin: True")
        print(f"   Active: True")
        print(f"   Premium: True")
        print("=" * 50)
        print("🔒 IMPORTANT: Save these credentials securely!")
        print("🌐 You can now login to the admin panel with these credentials")
        print("🔗 Admin login URL: http://localhost:3000/admin-login")
        
        # Verify the user was created
        cursor.execute("SELECT id, email, username, is_admin FROM users WHERE email = ?", (SUPERUSER_EMAIL,))
        result = cursor.fetchone()
        if result:
            print("✅ User verification: PASSED")
            print(f"   Created user: ID={result[0]}, Email={result[1]}, Username={result[2]}, Admin={result[3]}")
        else:
            print("❌ User verification: FAILED")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("⚠️  WARNING: This will permanently delete ALL users!")
    print("Creating superuser with email: aziz@bagbekov.ru")
    
    # Small delay to let user read the warning
    import time
    time.sleep(2)
    
    success = reset_and_create_superuser()
    
    if success:
        print("\n🎉 User reset completed successfully!")
        print("You can now access the admin panel with the new superuser credentials")
    else:
        print("\n💥 Failed to complete user reset")