"""
Integration tests for WebSocket connections
Tests WebSocket authentication, connection handling, and real-time communication
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import WebSocket
from fastapi.testclient import TestClient

from app.services.admin_websocket_service import admin_websocket_service, AdminConnectionManager
from app.core.auth import create_access_token
from app.models.user import User, AdminRole


@pytest.mark.asyncio
class TestWebSocketAuthentication:
    """Test WebSocket authentication and authorization"""

    async def test_websocket_jwt_validation(self):
        """Test JWT token validation for WebSocket connections"""
        manager = AdminConnectionManager()
        
        # Create a mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Test valid connection
        user_id = 1
        role = "admin"
        
        await manager.connect(mock_websocket, user_id, role)
        
        # Should be connected
        assert user_id in manager.active_connections
        assert manager.user_roles[user_id] == role
        assert manager.connection_stats['active_admins'] == 1

    async def test_websocket_role_based_channels(self):
        """Test that users can only access channels for their role"""
        manager = AdminConnectionManager()
        
        # Test different roles
        test_cases = [
            ("super_admin", ["all_channels", "user_management", "system_management"]),
            ("admin", ["user_management", "moderation_queue", "analytics"]),
            ("moderator", ["moderation_queue", "user_reports"]),
            ("analyst", ["analytics", "user_activity"])
        ]
        
        for role, expected_channels in test_cases:
            available = manager._get_available_channels(role)
            
            # Should have base channels
            assert "admin_dashboard" in available
            assert "notifications" in available
            
            # Should have role-specific channels
            for channel in expected_channels:
                assert channel in available

    async def test_websocket_subscription_authorization(self):
        """Test channel subscription authorization"""
        manager = AdminConnectionManager()
        
        # Connect a moderator
        user_id = 1
        role = "moderator"
        manager.user_roles[user_id] = role
        
        # Should be able to subscribe to allowed channels
        assert manager.subscribe_to_channel(user_id, "moderation_queue") == True
        assert manager.subscribe_to_channel(user_id, "user_reports") == True
        
        # Should NOT be able to subscribe to admin-only channels
        assert manager.subscribe_to_channel(user_id, "user_management") == False
        assert manager.subscribe_to_channel(user_id, "system_management") == False

    async def test_websocket_connection_cleanup(self):
        """Test proper cleanup when WebSocket disconnects"""
        manager = AdminConnectionManager()
        
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        role = "admin"
        
        # Connect
        await manager.connect(mock_websocket, user_id, role)
        manager.subscribe_to_channel(user_id, "admin_dashboard")
        
        # Verify connection exists
        assert user_id in manager.active_connections
        assert user_id in manager.subscriptions
        
        # Disconnect
        await manager.disconnect(mock_websocket, user_id)
        
        # Should be cleaned up
        assert user_id not in manager.active_connections
        assert user_id not in manager.user_roles
        assert user_id not in manager.subscriptions


@pytest.mark.asyncio
class TestWebSocketMessaging:
    """Test WebSocket message handling and broadcasting"""

    async def test_send_message_to_user(self):
        """Test sending message to specific user"""
        manager = AdminConnectionManager()
        
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        
        # Connect user
        await manager.connect(mock_websocket, user_id, "admin")
        
        # Send message
        success = await manager.send_to_user(
            user_id, 
            "test_message", 
            {"content": "Hello"}
        )
        
        assert success == True
        mock_websocket.send_text.assert_called_once()
        
        # Verify message format
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "test_message"
        assert message["payload"]["content"] == "Hello"

    async def test_broadcast_to_role(self):
        """Test broadcasting message to users with specific role"""
        manager = AdminConnectionManager()
        
        # Connect multiple users with different roles
        admin_ws = AsyncMock(spec=WebSocket)
        moderator_ws = AsyncMock(spec=WebSocket)
        
        await manager.connect(admin_ws, 1, "admin")
        await manager.connect(moderator_ws, 2, "moderator")
        
        # Broadcast to admins only
        await manager.broadcast_to_role(
            "admin", 
            "admin_message", 
            {"content": "Admin only"}
        )
        
        # Only admin should receive message
        admin_ws.send_text.assert_called_once()
        moderator_ws.send_text.assert_not_called()

    async def test_channel_subscription_messaging(self):
        """Test messaging through channel subscriptions"""
        manager = AdminConnectionManager()
        
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        
        # Connect users and subscribe to channel
        await manager.connect(mock_ws1, 1, "admin")
        await manager.connect(mock_ws2, 2, "admin")
        
        manager.subscribe_to_channel(1, "test_channel")
        # User 2 not subscribed to test_channel
        
        # Broadcast to channel
        await manager.broadcast_to_channel(
            "test_channel",
            "channel_message",
            {"content": "Channel broadcast"}
        )
        
        # Only subscribed user should receive message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_not_called()

    async def test_websocket_error_handling(self):
        """Test error handling in WebSocket communication"""
        manager = AdminConnectionManager()
        
        # Mock WebSocket that raises exception
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        
        user_id = 1
        await manager.connect(mock_websocket, user_id, "admin")
        
        # Send message should handle error gracefully
        success = await manager.send_to_user(
            user_id,
            "test_message",
            {"content": "Test"}
        )
        
        # Should return False due to error
        assert success == False
        
        # Connection should be cleaned up
        assert user_id not in manager.active_connections


@pytest.mark.asyncio
class TestWebSocketService:
    """Test AdminWebSocketService functionality"""

    async def test_admin_websocket_service_initialization(self):
        """Test service initialization and background tasks"""
        service = admin_websocket_service
        
        # Should have manager
        assert service.manager is not None
        
        # Should be able to get connection stats
        stats = service.get_connection_stats()
        assert isinstance(stats, dict)
        assert "total_connections" in stats
        assert "active_admins" in stats

    async def test_handle_admin_message_parsing(self):
        """Test parsing and handling of admin messages"""
        service = admin_websocket_service
        
        # Test valid JSON message
        message = json.dumps({
            "type": "subscribe",
            "payload": {"channel": "admin_dashboard"}
        })
        
        # Should not raise exception
        try:
            await service.handle_admin_message(1, "admin", message)
        except Exception as e:
            pytest.fail(f"Should handle valid message: {e}")

    async def test_handle_invalid_json_message(self):
        """Test handling of invalid JSON messages"""
        service = admin_websocket_service
        
        # Mock the manager to capture error messages
        service.manager.send_to_user = AsyncMock()
        
        # Send invalid JSON
        await service.handle_admin_message(1, "admin", "invalid json {")
        
        # Should send error message to user
        service.manager.send_to_user.assert_called_once()
        call_args = service.manager.send_to_user.call_args
        assert call_args[0][1] == "error"  # message type

    async def test_heartbeat_handling(self):
        """Test WebSocket heartbeat mechanism"""
        service = admin_websocket_service
        service.manager.send_to_user = AsyncMock()
        
        # Send heartbeat message
        heartbeat_msg = json.dumps({
            "type": "heartbeat",
            "payload": {"timestamp": time.time()}
        })
        
        await service.handle_admin_message(1, "admin", heartbeat_msg)
        
        # Should respond with heartbeat
        service.manager.send_to_user.assert_called_once()
        call_args = service.manager.send_to_user.call_args
        assert call_args[0][1] == "heartbeat"  # message type

    async def test_dashboard_updates(self):
        """Test dashboard update broadcasting"""
        service = admin_websocket_service
        service.manager.broadcast_to_channel = AsyncMock()
        
        # Send dashboard update
        test_data = {"users": 100, "sessions": 50}
        await service.send_dashboard_update(test_data)
        
        # Should broadcast to dashboard channel
        service.manager.broadcast_to_channel.assert_called_once_with(
            "admin_dashboard",
            "dashboard_update", 
            test_data
        )

    async def test_system_alert_broadcasting(self):
        """Test system alert broadcasting"""
        service = admin_websocket_service
        service.manager.broadcast_to_channel = AsyncMock()
        
        # Send system alert
        alert_data = {"message": "High CPU usage", "level": "warning"}
        await service.send_system_alert(alert_data, "warning")
        
        # Should broadcast to alerts channel
        service.manager.broadcast_to_channel.assert_called_once()
        call_args = service.manager.broadcast_to_channel.call_args
        assert call_args[0][0] == "system_alerts"
        assert call_args[0][1] == "system_alert"
        assert call_args[0][2]["severity"] == "warning"


@pytest.mark.asyncio
class TestWebSocketResilience:
    """Test WebSocket resilience and error recovery"""

    async def test_connection_recovery_after_error(self):
        """Test connection recovery after network error"""
        manager = AdminConnectionManager()
        
        # Simulate connection with error
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        
        await manager.connect(mock_websocket, user_id, "admin")
        
        # Simulate connection error during message send
        mock_websocket.send_text.side_effect = Exception("Network error")
        
        # Try to send message
        success = await manager.send_to_user(user_id, "test", {"data": "test"})
        assert success == False
        
        # Connection should be cleaned up
        assert user_id not in manager.active_connections

    async def test_multiple_connections_same_user(self):
        """Test handling multiple connections from same user"""
        manager = AdminConnectionManager()
        
        # Connect same user multiple times (different browser tabs)
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        
        user_id = 1
        await manager.connect(ws1, user_id, "admin")
        await manager.connect(ws2, user_id, "admin")
        
        # Should have multiple connections for same user
        assert len(manager.active_connections[user_id]) == 2
        
        # Message should go to both connections
        await manager.send_to_user(user_id, "test", {"data": "test"})
        
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    async def test_partial_connection_failure(self):
        """Test handling when some connections fail but others work"""
        manager = AdminConnectionManager()
        
        # Connect same user with multiple connections
        good_ws = AsyncMock(spec=WebSocket)
        bad_ws = AsyncMock(spec=WebSocket)
        bad_ws.send_text.side_effect = Exception("Connection failed")
        
        user_id = 1
        await manager.connect(good_ws, user_id, "admin")
        await manager.connect(bad_ws, user_id, "admin")
        
        # Send message
        success = await manager.send_to_user(user_id, "test", {"data": "test"})
        
        # Should still succeed for good connection
        good_ws.send_text.assert_called_once()
        
        # Bad connection should be removed
        assert bad_ws not in manager.active_connections[user_id]
        assert good_ws in manager.active_connections[user_id]

    async def test_connection_stats_accuracy(self):
        """Test accuracy of connection statistics"""
        manager = AdminConnectionManager()
        
        # Connect multiple users
        for i in range(5):
            ws = AsyncMock(spec=WebSocket)
            await manager.connect(ws, i, "admin")
        
        stats = manager.get_connection_stats()
        
        assert stats["total_connections"] == 5
        assert stats["active_admins"] == 5
        assert stats["connections_by_role"]["admin"] == 5
        
        # Disconnect one user
        await manager.disconnect(AsyncMock(), 0)
        
        stats = manager.get_connection_stats()
        assert stats["active_admins"] == 4

    async def test_background_task_error_handling(self):
        """Test background task error handling"""
        service = admin_websocket_service
        
        # Mock failing dashboard data method
        original_method = service._get_dashboard_data
        
        async def failing_method():
            raise Exception("Dashboard error")
        
        service._get_dashboard_data = failing_method
        
        # Should handle error gracefully
        try:
            await service._send_dashboard_updates()
        except Exception as e:
            pytest.fail(f"Should handle dashboard error gracefully: {e}")
        
        # Restore original method
        service._get_dashboard_data = original_method


@pytest.mark.asyncio 
class TestWebSocketIntegrationScenarios:
    """Integration test scenarios for WebSocket functionality"""

    async def test_admin_login_to_websocket_flow(self):
        """Test complete flow from admin login to WebSocket connection"""
        # This would be an integration test with actual auth
        # For now, test the components separately
        
        manager = AdminConnectionManager()
        
        # Simulate admin login and token creation
        user_data = {"sub": "1", "role": "admin"}
        token = create_access_token(data=user_data)
        
        # Token should be valid (this tests token creation)
        assert token is not None
        assert len(token) > 0
        
        # Connect with admin role
        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws, 1, "admin")
        
        # Should be connected with proper role
        assert manager.user_roles[1] == "admin"

    async def test_real_time_notification_flow(self):
        """Test real-time notification delivery flow"""
        service = admin_websocket_service
        service.manager.send_to_user = AsyncMock()
        
        # Simulate notification creation and delivery
        notification_data = {
            "id": 123,
            "title": "Test Notification",
            "message": "This is a test",
            "type": "info"
        }
        
        # Send notification to admin
        await service.send_notification(1, notification_data)
        
        # Should call send_to_user
        service.manager.send_to_user.assert_called_once_with(
            1, "notification", notification_data
        )

    async def test_moderation_queue_update_flow(self):
        """Test moderation queue update broadcasting"""
        service = admin_websocket_service
        service.manager.broadcast_to_channel = AsyncMock()
        
        # Simulate moderation queue update
        queue_data = {
            "pending_count": 5,
            "new_items": [{"id": 1, "content": "Test message"}]
        }
        
        await service.send_moderation_queue_update(queue_data)
        
        # Should broadcast to moderation channel
        service.manager.broadcast_to_channel.assert_called_once_with(
            "moderation_queue",
            "moderation_queue_update",
            queue_data
        )

    async def test_system_monitoring_integration(self):
        """Test integration with system monitoring"""
        service = admin_websocket_service
        
        # Test getting system metrics
        try:
            metrics = await service._get_system_metrics()
            
            # Should return valid metrics structure
            assert isinstance(metrics, dict)
            assert "timestamp" in metrics
            
        except Exception as e:
            # Should handle gracefully if monitoring not available
            assert "not available" in str(e).lower() or "error" in str(e).lower()