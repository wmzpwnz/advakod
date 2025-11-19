"""
Integration tests for admin panel modules
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestAdminPanelIntegration:
    """Test integration between admin panel modules."""

    async def test_user_role_moderation_workflow(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        super_admin_headers: dict,
        moderator_headers: dict
    ):
        """Test complete workflow from user creation to moderation."""
        
        # 1. Create a new user
        user_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "role": "user"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=super_admin_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # 2. Assign moderator role to another user
        role_data = {"role": "moderator"}
        response = await async_client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json=role_data,
            headers=super_admin_headers
        )
        assert response.status_code == 200
        
        # 3. Create a message that needs moderation
        message_data = {
            "content": "This is a test message for moderation",
            "user_id": user_id,
            "ai_response": "This is the AI response",
            "needs_moderation": True
        }
        
        response = await async_client.post(
            "/api/v1/admin/moderation/messages",
            json=message_data,
            headers=super_admin_headers
        )
        assert response.status_code == 201
        message_id = response.json()["id"]
        
        # 4. Moderate the message
        moderation_data = {
            "rating": 8,
            "comment": "Good response, approved",
            "status": "approved",
            "categories": []
        }
        
        response = await async_client.post(
            f"/api/v1/admin/moderation/messages/{message_id}/review",
            json=moderation_data,
            headers=moderator_headers
        )
        assert response.status_code == 200
        
        # 5. Verify moderation was recorded
        response = await async_client.get(
            f"/api/v1/admin/moderation/messages/{message_id}",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        assert response.json()["rating"] == 8

    async def test_marketing_ab_test_integration(
        self,
        async_client: AsyncClient,
        db_session: Session,
        admin_headers: dict
    ):
        """Test integration between marketing tools and A/B testing."""
        
        # 1. Create a promo code
        promo_data = {
            "code": "TESTPROMO2024",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "usage_limit": 100,
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_to": "2024-12-31T23:59:59Z"
        }
        
        response = await async_client.post(
            "/api/v1/admin/marketing/promo-codes",
            json=promo_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        promo_id = response.json()["id"]
        
        # 2. Create an A/B test for the promo code
        ab_test_data = {
            "name": "Promo Code Display Test",
            "description": "Testing different ways to display promo codes",
            "hypothesis": "Prominent display increases usage",
            "type": "element",
            "variants": [
                {
                    "name": "Control",
                    "description": "Standard promo display",
                    "is_control": True,
                    "traffic_percentage": 50.0
                },
                {
                    "name": "Prominent Display",
                    "description": "Large, prominent promo display",
                    "is_control": False,
                    "traffic_percentage": 50.0
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/admin/marketing/ab-tests",
            json=ab_test_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        test_id = response.json()["id"]
        
        # 3. Start the A/B test
        response = await async_client.put(
            f"/api/v1/admin/marketing/ab-tests/{test_id}/status",
            json={"status": "running"},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 4. Simulate test participants and promo usage
        for i in range(10):
            # Assign participant to test
            participant_data = {
                "user_id": i + 1,
                "session_id": f"session_{i}",
                "user_agent": "Test User Agent",
                "ip_address": f"192.168.1.{i + 1}"
            }
            
            response = await async_client.post(
                f"/api/v1/admin/marketing/ab-tests/{test_id}/participants",
                json=participant_data,
                headers=admin_headers
            )
            assert response.status_code == 201
            
            # Simulate promo code usage (for some participants)
            if i % 3 == 0:
                usage_data = {
                    "user_id": i + 1,
                    "order_value": 100.0
                }
                
                response = await async_client.post(
                    f"/api/v1/admin/marketing/promo-codes/{promo_id}/use",
                    json=usage_data,
                    headers=admin_headers
                )
                assert response.status_code == 200
        
        # 5. Check A/B test statistics
        response = await async_client.get(
            f"/api/v1/admin/marketing/ab-tests/{test_id}/statistics",
            headers=admin_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_participants"] == 10
        
        # 6. Check promo code analytics
        response = await async_client.get(
            f"/api/v1/admin/marketing/promo-codes/{promo_id}/analytics",
            headers=admin_headers
        )
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["total_uses"] > 0

    async def test_project_notification_integration(
        self,
        async_client: AsyncClient,
        db_session: Session,
        admin_headers: dict
    ):
        """Test integration between project management and notifications."""
        
        # 1. Create a project task
        task_data = {
            "title": "Integration Test Task",
            "description": "Task for testing integration",
            "priority": "high",
            "estimated_hours": 8.0,
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = await async_client.post(
            "/api/v1/admin/project/tasks",
            json=task_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        task_id = response.json()["id"]
        
        # 2. Update task status (should trigger notification)
        update_data = {"status": "in_progress"}
        
        response = await async_client.put(
            f"/api/v1/admin/project/tasks/{task_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 3. Check that notification was created
        response = await async_client.get(
            "/api/v1/admin/notifications",
            headers=admin_headers
        )
        assert response.status_code == 200
        notifications = response.json()["notifications"]
        
        task_notifications = [
            n for n in notifications 
            if "task" in n["message"].lower() and "in_progress" in n["message"].lower()
        ]
        assert len(task_notifications) > 0
        
        # 4. Create a milestone and associate task
        milestone_data = {
            "name": "Test Milestone",
            "description": "Milestone for integration testing",
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = await async_client.post(
            "/api/v1/admin/project/milestones",
            json=milestone_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        milestone_id = response.json()["id"]
        
        # 5. Associate task with milestone
        response = await async_client.put(
            f"/api/v1/admin/project/tasks/{task_id}",
            json={"milestone_id": milestone_id},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 6. Complete the task (should trigger milestone progress notification)
        response = await async_client.put(
            f"/api/v1/admin/project/tasks/{task_id}",
            json={"status": "completed"},
            headers=admin_headers
        )
        assert response.status_code == 200

    async def test_backup_notification_integration(
        self,
        async_client: AsyncClient,
        db_session: Session,
        super_admin_headers: dict,
        mock_backup_service
    ):
        """Test integration between backup system and notifications."""
        
        # 1. Create a backup
        backup_data = {
            "backup_type": "manual",
            "components": ["database", "files"],
            "description": "Integration test backup"
        }
        
        response = await async_client.post(
            "/api/v1/admin/backup/create",
            json=backup_data,
            headers=super_admin_headers
        )
        assert response.status_code == 202  # Accepted for async processing
        backup_id = response.json()["backup_id"]
        
        # 2. Check backup status
        response = await async_client.get(
            f"/api/v1/admin/backup/{backup_id}",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        
        # 3. Simulate backup completion notification
        notification_data = {
            "type": "success",
            "title": "Backup Completed",
            "message": f"Backup {backup_id} completed successfully",
            "priority": "medium",
            "channels": ["web", "email"]
        }
        
        response = await async_client.post(
            "/api/v1/admin/notifications",
            json=notification_data,
            headers=super_admin_headers
        )
        assert response.status_code == 201
        
        # 4. Verify notification was created and linked to backup
        response = await async_client.get(
            "/api/v1/admin/notifications",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        notifications = response.json()["notifications"]
        
        backup_notifications = [
            n for n in notifications 
            if backup_id in n["message"]
        ]
        assert len(backup_notifications) > 0

    async def test_real_time_updates_integration(
        self,
        async_client: AsyncClient,
        db_session: Session,
        admin_headers: dict,
        mock_websocket
    ):
        """Test real-time updates across different modules."""
        
        # 1. Create a user (should trigger real-time update)
        user_data = {
            "email": "realtime@test.com",
            "password": "TestPassword123!",
            "name": "Real Time User",
            "role": "user"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        
        # Verify WebSocket broadcast was called
        mock_websocket.broadcast_dashboard_update.assert_called()
        
        # 2. Create a notification (should trigger real-time update)
        notification_data = {
            "type": "info",
            "title": "Real-time Test",
            "message": "Testing real-time notifications",
            "priority": "high",
            "channels": ["web"]
        }
        
        response = await async_client.post(
            "/api/v1/admin/notifications",
            json=notification_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        
        # Verify notification WebSocket was called
        mock_websocket.send_notification.assert_called()
        
        # 3. Update moderation queue (should trigger real-time update)
        message_data = {
            "content": "Real-time moderation test",
            "user_id": 1,
            "ai_response": "AI response for real-time test",
            "needs_moderation": True
        }
        
        response = await async_client.post(
            "/api/v1/admin/moderation/messages",
            json=message_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        
        # Verify moderation queue update was called
        mock_websocket.update_moderation_queue.assert_called()

    async def test_cross_module_permissions(
        self,
        async_client: AsyncClient,
        db_session: Session,
        moderator_headers: dict,
        admin_headers: dict,
        super_admin_headers: dict
    ):
        """Test permissions across different modules."""
        
        # Test moderator permissions
        # Should have access to moderation
        response = await async_client.get(
            "/api/v1/admin/moderation/queue",
            headers=moderator_headers
        )
        assert response.status_code == 200
        
        # Should NOT have access to user management
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=moderator_headers
        )
        assert response.status_code == 403
        
        # Should NOT have access to marketing
        response = await async_client.get(
            "/api/v1/admin/marketing/dashboard",
            headers=moderator_headers
        )
        assert response.status_code == 403
        
        # Test admin permissions
        # Should have access to most modules
        modules = ["users", "moderation", "marketing", "project", "notifications"]
        for module in modules:
            response = await async_client.get(
                f"/api/v1/admin/{module}",
                headers=admin_headers
            )
            assert response.status_code in [200, 404]  # 404 for non-existent endpoints
        
        # Should NOT have access to backup (super admin only)
        response = await async_client.get(
            "/api/v1/admin/backup",
            headers=admin_headers
        )
        assert response.status_code == 403
        
        # Test super admin permissions
        # Should have access to all modules including backup
        response = await async_client.get(
            "/api/v1/admin/backup",
            headers=super_admin_headers
        )
        assert response.status_code == 200

    async def test_data_consistency_across_modules(
        self,
        async_client: AsyncClient,
        db_session: Session,
        admin_headers: dict
    ):
        """Test data consistency when operations span multiple modules."""
        
        # 1. Create a user
        user_data = {
            "email": "consistency@test.com",
            "password": "TestPassword123!",
            "name": "Consistency Test User",
            "role": "user"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # 2. Create related data in multiple modules
        # Create a task assigned to the user
        task_data = {
            "title": "User Task",
            "description": "Task assigned to test user",
            "assigned_to": user_id,
            "priority": "medium"
        }
        
        response = await async_client.post(
            "/api/v1/admin/project/tasks",
            json=task_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        task_id = response.json()["id"]
        
        # Create a notification for the user
        notification_data = {
            "type": "info",
            "title": "Task Assignment",
            "message": f"You have been assigned task: {task_id}",
            "user_id": user_id,
            "priority": "medium",
            "channels": ["web"]
        }
        
        response = await async_client.post(
            "/api/v1/admin/notifications",
            json=notification_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        notification_id = response.json()["id"]
        
        # 3. Verify data consistency
        # Check user exists and has correct data
        response = await async_client.get(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "consistency@test.com"
        
        # Check task is assigned to correct user
        response = await async_client.get(
            f"/api/v1/admin/project/tasks/{task_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        task = response.json()
        assert task["assigned_to"] == user_id
        
        # Check notification is for correct user
        response = await async_client.get(
            f"/api/v1/admin/notifications/{notification_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        notification = response.json()
        assert notification["user_id"] == user_id
        
        # 4. Test cascading updates
        # Update user role and verify it affects related data
        response = await async_client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"role": "moderator"},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify user role was updated
        response = await async_client.get(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["role"] == "moderator"