"""
Test configuration and fixtures for comprehensive testing
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis
from unittest.mock import Mock, AsyncMock

from main import app
from app.core.config import settings
from app.models import Base
from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.models.user import User, AdminRole
from app.models.notification import AdminNotification
from app.models.backup import BackupRecord
from app.models.ab_testing import ABTest, ABTestVariant
from app.models.project import Task, ProjectMilestone


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session):
    """Create an async test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=True)
    mock_redis.exists = Mock(return_value=False)
    mock_redis.expire = Mock(return_value=True)
    return mock_redis


@pytest.fixture
def super_admin_user(db_session):
    """Create a super admin user for testing."""
    user = User(
        email="superadmin@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        is_active=True,
        role=AdminRole.SUPER_ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        email="admin@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        is_active=True,
        role=AdminRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def moderator_user(db_session):
    """Create a moderator user for testing."""
    user = User(
        email="moderator@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        is_active=True,
        role=AdminRole.MODERATOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular user for testing."""
    user = User(
        email="user@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        is_active=True,
        role=AdminRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create an admin JWT token for testing."""
    from app.core.auth import create_access_token
    return create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})


@pytest.fixture
def super_admin_token(super_admin_user):
    """Create a super admin JWT token for testing."""
    from app.core.auth import create_access_token
    return create_access_token(data={"sub": str(super_admin_user.id), "role": super_admin_user.role.value})


@pytest.fixture
def moderator_token(moderator_user):
    """Create a moderator JWT token for testing."""
    from app.core.auth import create_access_token
    return create_access_token(data={"sub": str(moderator_user.id), "role": moderator_user.role.value})


@pytest.fixture
def auth_headers(admin_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def super_admin_headers(super_admin_token):
    """Create super admin authorization headers for testing."""
    return {"Authorization": f"Bearer {super_admin_token}"}


@pytest.fixture
def moderator_headers(moderator_token):
    """Create moderator authorization headers for testing."""
    return {"Authorization": f"Bearer {moderator_token}"}


@pytest.fixture
def sample_notification(db_session, admin_user):
    """Create a sample notification for testing."""
    notification = AdminNotification(
        type="info",
        title="Test Notification",
        message="This is a test notification",
        user_id=admin_user.id,
        priority="medium",
        channels=["web"]
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


@pytest.fixture
def sample_backup(db_session):
    """Create a sample backup for testing."""
    backup = BackupRecord(
        name="test_backup",
        backup_type="manual",
        status="completed",
        backup_path="/backups/test_backup.sql",
        total_size=1024000,
        components={"database": True, "files": True}
    )
    db_session.add(backup)
    db_session.commit()
    db_session.refresh(backup)
    return backup


@pytest.fixture
def sample_ab_test(db_session, admin_user):
    """Create a sample A/B test for testing."""
    from app.models.ab_testing import ABTestStatus, ABTestType, PrimaryMetric
    
    ab_test = ABTest(
        name="Test Button Color",
        description="Testing button colors",
        hypothesis="Red buttons convert better",
        type=ABTestType.ELEMENT,
        status=ABTestStatus.DRAFT,
        creator_id=admin_user.id,
        traffic_allocation=100.0,
        duration=14,
        sample_size=1000,
        confidence_level=95.0,
        primary_metric=PrimaryMetric.CONVERSION_RATE
    )
    db_session.add(ab_test)
    db_session.commit()
    db_session.refresh(ab_test)
    
    # Add variants
    variant1 = ABTestVariant(
        test_id=ab_test.id,
        name="Control",
        description="Original blue button",
        is_control=True,
        traffic_percentage=50.0
    )
    variant2 = ABTestVariant(
        test_id=ab_test.id,
        name="Variant A",
        description="Red button",
        is_control=False,
        traffic_percentage=50.0
    )
    
    db_session.add_all([variant1, variant2])
    db_session.commit()
    
    return ab_test


@pytest.fixture
def sample_task(db_session, admin_user):
    """Create a sample task for testing."""
    from app.models.project import TaskStatus, TaskPriority
    
    task = Task(
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        assigned_to=admin_user.id,
        created_by=admin_user.id,
        estimated_hours=8.0
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def mock_websocket():
    """Mock WebSocket manager for testing."""
    mock_ws = AsyncMock()
    mock_ws.broadcast_dashboard_update = AsyncMock()
    mock_ws.send_notification = AsyncMock()
    mock_ws.update_moderation_queue = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock_email = AsyncMock()
    mock_email.send_notification = AsyncMock(return_value=True)
    mock_email.send_bulk_notifications = AsyncMock(return_value=True)
    return mock_email


@pytest.fixture
def mock_backup_service():
    """Mock backup service for testing."""
    mock_backup = AsyncMock()
    mock_backup.create_backup = AsyncMock(return_value="backup_123.sql")
    mock_backup.restore_backup = AsyncMock(return_value=True)
    mock_backup.validate_backup = AsyncMock(return_value=True)
    return mock_backup


@pytest.fixture
def performance_test_data():
    """Generate test data for performance testing."""
    return {
        "users": [
            {
                "email": f"user{i}@test.com",
                "name": f"Test User {i}",
                "role": "user",
                "is_active": True
            }
            for i in range(1000)
        ],
        "notifications": [
            {
                "type": "info",
                "title": f"Notification {i}",
                "message": f"Test notification message {i}",
                "priority": "medium"
            }
            for i in range(500)
        ]
    }


@pytest.fixture
def security_test_payloads():
    """Common security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM admin_users --",
            "'; INSERT INTO users (email) VALUES ('hacked@test.com'); --"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Custom pytest hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add integration marker for tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker for tests in performance directory
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Add security marker for tests in security directory
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)