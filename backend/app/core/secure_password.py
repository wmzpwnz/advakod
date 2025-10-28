"""
Secure password hashing service using industry best practices
"""

from passlib.context import CryptContext
from passlib.hash import argon2, bcrypt
import logging

logger = logging.getLogger(__name__)

# Create password context with secure schemes
# Argon2 is the current OWASP recommendation, with bcrypt as fallback
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    # Argon2 parameters (OWASP recommended)
    argon2__time_cost=3,      # Number of iterations
    argon2__memory_cost=65536, # Memory usage in KiB (64 MB)
    argon2__parallelism=1,     # Number of threads
    # Bcrypt parameters
    bcrypt__rounds=12,         # Number of rounds (2^12 = 4096)
)


def hash_password(password: str) -> str:
    """
    Hash a password using secure algorithms
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty or invalid
    """
    if not password or len(password.strip()) == 0:
        raise ValueError("Password cannot be empty")
        
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
        
    try:
        hashed = pwd_context.hash(password)
        logger.info("Password hashed successfully using secure algorithm")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
        
    try:
        # Verify password and check if hash needs upgrading
        is_valid, needs_update = pwd_context.verify_and_update(plain_password, hashed_password)
        
        if needs_update:
            logger.info("Password hash needs updating to newer algorithm")
            # In a real application, you would update the hash in the database here
            
        return is_valid
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def needs_rehashing(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated to a stronger algorithm
    
    Args:
        hashed_password: The hash to check
        
    Returns:
        True if hash should be upgraded, False otherwise
    """
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception:
        return True  # If we can't identify the hash, it probably needs updating


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password
    
    Args:
        length: Length of password to generate (minimum 12)
        
    Returns:
        Secure random password
    """
    import secrets
    import string
    
    if length < 12:
        length = 12
        
    # Character set for password generation
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    
    # Generate secure random password
    password = ''.join(secrets.choice(chars) for _ in range(length))
    
    # Ensure password has at least one of each character type
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)  
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in "!@#$%^&*()_+-=" for c in password):
        password = password[:-1] + secrets.choice("!@#$%^&*()_+-=")
        
    return password


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
        
    if len(password) > 128:
        issues.append("Password must be less than 128 characters")
        
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
        
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
        
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
        
    # Check for common weak passwords
    weak_passwords = [
        "password", "123456", "qwerty", "admin", "letmein", 
        "welcome", "monkey", "1234567890", "password123"
    ]
    
    if password.lower() in weak_passwords:
        issues.append("Password is too common and easily guessable")
        
    return len(issues) == 0, issues