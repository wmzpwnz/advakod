"""
Core module for Advakod backend application.
Contains configuration, database, and security setup.
"""

from .config import settings
from .database import SessionLocal, get_db, Base
from .security import (
    validate_and_sanitize_query,
    create_secure_ai_prompt,
    validate_file_type,
    validate_file_size,
    input_sanitizer,
    security_audit_logger
)

__all__ = [
    "settings",
    "SessionLocal", 
    "get_db",
    "Base",
    "validate_and_sanitize_query",
    "create_secure_ai_prompt", 
    "validate_file_type",
    "validate_file_size",
    "input_sanitizer",
    "security_audit_logger"
]
