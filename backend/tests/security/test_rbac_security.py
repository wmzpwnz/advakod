"""
Security tests for RBAC system and admin panel
"""
import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.orm import Session


@pytest.mark.security
class TestRBACSecurityTests:
    """Security tests for Role-Based Access Control system."""

    async def test_unauthorized_access_prevention(
        self,
        async_client: AsyncClient
    ):
        """Test that unauthorized access is properly prevented."""
        
        # Test access without any token
        protected_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/roles",
            "/api/v1/admin/moderation/queue",
            "/api/v1/admin/marketing/dashboard",
            "/api/v1/admin/project/tasks",
            "/api/v1/admin/notifications",
            "/api/v1/admin/backup"
        ]
        
        for endpoint in protected_endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
            assert "detail" in response.json()

    async def test_invalid_token_handling(
        self,
        async_client: AsyncClient
    ):
        """Test handling of invalid JWT tokens."""
        
        invalid_tokens = [
            "invalid.token.here",
            "Bearer invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "",
            "Bearer ",
            "malformed_token_without_dots"
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": token} if token else {}
            
            response = await async_client.get(
                "/api/v1/admin/users",
                headers=headers
            )
            
            assert response.status_code == 401
            error_detail = response.json().get("detail", "")
            assert any(keyword in error_detail.lower() for keyword in ["invalid", "token", "unauthorized"])

    async def test_expired_token_handling(
        self,
        async_client: AsyncClient
    ):
        """Test handling of expired JWT tokens."""
        
        from app.core.config import settings
        
        # Create an expired token
        expired_payload = {
            "sub": "1",
            "role": "admin",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=headers
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_role_based_access_enforcement(
        self,
        async_client: AsyncClient,
        moderator_headers: dict,
        admin_headers: dict,
        super_admin_headers: dict
    ):
        """Test that role-based access is properly enforced."""
        
        # Test moderator access restrictions
        moderator_forbidden_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/roles",
            "/api/v1/admin/marketing/dashboard",
            "/api/v1/admin/project/tasks",
            "/api/v1/admin/backup"
        ]
        
        for endpoint in moderator_forbidden_endpoints:
            response = await async_client.get(endpoint, headers=moderator_headers)
            assert response.status_code == 403  # Forbidden
        
        # Test moderator allowed endpoints
        moderator_allowed_endpoints = [
            "/api/v1/admin/moderation/queue",
            "/api/v1/admin/moderation/messages"
        ]
        
        for endpoint in moderator_allowed_endpoints:
            response = await async_client.get(endpoint, headers=moderator_headers)
            assert response.status_code in [200, 404]  # 404 for non-existent specific endpoints
        
        # Test admin access (should have more access than moderator)
        admin_allowed_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/moderation/queue",
            "/api/v1/admin/marketing/dashboard",
            "/api/v1/admin/project/tasks",
            "/api/v1/admin/notifications"
        ]
        
        for endpoint in admin_allowed_endpoints:
            response = await async_client.get(endpoint, headers=admin_headers)
            assert response.status_code in [200, 404]
        
        # Test admin restrictions (should not access backup)
        response = await async_client.get("/api/v1/admin/backup", headers=admin_headers)
        assert response.status_code == 403
        
        # Test super admin access (should access everything)
        response = await async_client.get("/api/v1/admin/backup", headers=super_admin_headers)
        assert response.status_code == 200

    async def test_privilege_escalation_prevention(
        self,
        async_client: AsyncClient,
        moderator_headers: dict,
        admin_headers: dict,
        db_session: Session,
        regular_user
    ):
        """Test prevention of privilege escalation attacks."""
        
        # Test moderator trying to assign admin role
        role_escalation_data = {"role": "admin"}
        
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/role",
            json=role_escalation_data,
            headers=moderator_headers
        )
        assert response.status_code == 403
        
        # Test admin trying to assign super_admin role
        super_admin_escalation_data = {"role": "super_admin"}
        
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/role",
            json=super_admin_escalation_data,
            headers=admin_headers
        )
        assert response.status_code == 403
        
        # Test user trying to modify their own role via API manipulation
        user_token = self._create_user_token(regular_user.id, "user")
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.put(
            f"/api/v1/admin/users/{regular_user.id}/role",
            json={"role": "admin"},
            headers=user_headers
        )
        assert response.status_code in [401, 403]  # Should be denied

    async def test_sql_injection_prevention(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        security_test_payloads: dict
    ):
        """Test prevention of SQL injection attacks."""
        
        sql_payloads = security_test_payloads["sql_injection"]
        
        # Test SQL injection in search parameters
        for payload in sql_payloads:
            response = await async_client.get(
                f"/api/v1/admin/users?search={payload}",
                headers=admin_headers
            )
            
            # Should not cause database errors
            assert response.status_code in [200, 400]  # 400 for invalid input
            
            if response.status_code == 200:
                # Should not return unexpected data
                data = response.json()
                assert "users" in data
                assert isinstance(data["users"], list)
            
            # Response should not contain SQL error messages
            response_text = response.text.lower()
            sql_error_indicators = ["sql", "syntax error", "database", "mysql", "postgresql"]
            for indicator in sql_error_indicators:
                assert indicator not in response_text

    async def test_xss_prevention(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        security_test_payloads: dict,
        db_session: Session
    ):
        """Test prevention of XSS attacks."""
        
        xss_payloads = security_test_payloads["xss_payloads"]
        
        # Test XSS in user creation
        for payload in xss_payloads:
            user_data = {
                "email": "xsstest@example.com",
                "password": "TestPassword123!",
                "name": payload,  # XSS payload in name field
                "role": "user"
            }
            
            response = await async_client.post(
                "/api/v1/admin/users",
                json=user_data,
                headers=admin_headers
            )
            
            if response.status_code == 201:
                # If user was created, verify XSS payload is sanitized
                user_id = response.json()["id"]
                
                response = await async_client.get(
                    f"/api/v1/admin/users/{user_id}",
                    headers=admin_headers
                )
                
                assert response.status_code == 200
                user_data = response.json()
                
                # Name should not contain script tags or other XSS vectors
                name = user_data["name"]
                dangerous_patterns = ["<script", "<img", "javascript:", "onerror=", "onload="]
                for pattern in dangerous_patterns:
                    assert pattern.lower() not in name.lower()
                
                # Clean up
                await async_client.delete(
                    f"/api/v1/admin/users/{user_id}",
                    headers=admin_headers
                )

    async def test_csrf_protection(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test CSRF protection mechanisms."""
        
        # Test request with suspicious origin
        malicious_headers = {
            **admin_headers,
            "Origin": "https://malicious-site.com",
            "Referer": "https://malicious-site.com/attack"
        }
        
        user_data = {
            "email": "csrf@example.com",
            "password": "TestPassword123!",
            "name": "CSRF Test User",
            "role": "admin"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=malicious_headers
        )
        
        # Should be rejected due to CORS/CSRF protection
        assert response.status_code in [400, 403]

    async def test_rate_limiting_security(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test rate limiting for security-sensitive operations."""
        
        # Test rapid role assignment attempts (potential privilege escalation)
        user_data = {
            "email": "ratelimit@example.com",
            "password": "TestPassword123!",
            "name": "Rate Limit Test",
            "role": "user"
        }
        
        # Create a user first
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Attempt rapid role changes
        rate_limited_responses = 0
        for i in range(20):
            role_data = {"role": "moderator" if i % 2 == 0 else "user"}
            
            response = await async_client.put(
                f"/api/v1/admin/users/{user_id}/role",
                json=role_data,
                headers=admin_headers
            )
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited_responses += 1
        
        # Should have some rate limiting
        assert rate_limited_responses > 0

    async def test_input_validation_security(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test input validation for security."""
        
        # Test oversized inputs
        oversized_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": "A" * 10000,  # Extremely long name
            "role": "user"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=oversized_data,
            headers=admin_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test invalid email formats
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            ""
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "password": "TestPassword123!",
                "name": "Test User",
                "role": "user"
            }
            
            response = await async_client.post(
                "/api/v1/admin/users",
                json=user_data,
                headers=admin_headers
            )
            assert response.status_code == 422

    async def test_password_security_requirements(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test password security requirements."""
        
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "qwerty",
            "12345678",
            "abc123",
            "password123"
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "email": f"weakpass{weak_password}@example.com",
                "password": weak_password,
                "name": "Weak Password Test",
                "role": "user"
            }
            
            response = await async_client.post(
                "/api/v1/admin/users",
                json=user_data,
                headers=admin_headers
            )
            
            # Should reject weak passwords
            assert response.status_code == 422
            error_detail = response.json()["detail"]
            assert any("password" in str(error).lower() for error in error_detail)

    async def test_session_security(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test session security mechanisms."""
        
        # Test that tokens have reasonable expiration
        from app.core.auth import create_access_token
        
        # Create token with very short expiration
        short_token = create_access_token(
            data={"sub": "1", "role": "admin"},
            expires_delta=timedelta(seconds=1)
        )
        
        # Wait for token to expire
        import asyncio
        await asyncio.sleep(2)
        
        headers = {"Authorization": f"Bearer {short_token}"}
        response = await async_client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code == 401

    async def test_file_upload_security(
        self,
        async_client: AsyncClient,
        super_admin_headers: dict
    ):
        """Test file upload security for backup operations."""
        
        # Test malicious file types
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.js", b"alert('xss')", "application/javascript"),
            ("backdoor.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("virus.bat", b"@echo off\ndel /f /q *.*", "application/x-msdos-program")
        ]
        
        for filename, content, mime_type in malicious_files:
            files = {"file": (filename, content, mime_type)}
            
            response = await async_client.post(
                "/api/v1/admin/backup/upload",
                files=files,
                headers=super_admin_headers
            )
            
            # Should reject malicious file types
            assert response.status_code in [400, 422]
            error_message = response.json().get("detail", "").lower()
            assert any(keyword in error_message for keyword in ["invalid", "not allowed", "forbidden"])

    def _create_user_token(self, user_id: int, role: str) -> str:
        """Helper method to create a user token for testing."""
        from app.core.auth import create_access_token
        return create_access_token(data={"sub": str(user_id), "role": role})

    async def test_api_versioning_security(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test that API versioning doesn't expose security vulnerabilities."""
        
        # Test access to non-existent API versions
        invalid_versions = [
            "/api/v0/admin/users",
            "/api/v2/admin/users",
            "/api/v1.1/admin/users",
            "/api/admin/users",  # Missing version
            "/admin/users"  # Missing API prefix
        ]
        
        for endpoint in invalid_versions:
            response = await async_client.get(endpoint, headers=admin_headers)
            assert response.status_code == 404

    async def test_information_disclosure_prevention(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test prevention of information disclosure."""
        
        # Test that error messages don't reveal sensitive information
        response = await async_client.get(
            "/api/v1/admin/users/99999",  # Non-existent user
            headers=admin_headers
        )
        
        assert response.status_code == 404
        error_message = response.json()["detail"].lower()
        
        # Should not reveal database structure or internal details
        sensitive_terms = ["table", "column", "database", "sql", "query", "internal"]
        for term in sensitive_terms:
            assert term not in error_message

    async def test_concurrent_session_security(
        self,
        async_client: AsyncClient,
        admin_user,
        db_session: Session
    ):
        """Test security with concurrent sessions."""
        
        from app.core.auth import create_access_token
        
        # Create multiple tokens for the same user
        token1 = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})
        token2 = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Both tokens should work initially
        response1 = await async_client.get("/api/v1/admin/users", headers=headers1)
        response2 = await async_client.get("/api/v1/admin/users", headers=headers2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Test that sensitive operations are properly tracked
        # (This would typically involve session management and audit logging)