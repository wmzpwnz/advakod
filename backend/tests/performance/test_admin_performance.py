"""
Performance tests for admin panel functionality
"""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from httpx import AsyncClient
from sqlalchemy.orm import Session


@pytest.mark.performance
class TestAdminPerformance:
    """Performance tests for admin panel operations."""

    async def test_dashboard_load_performance(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        performance_test_data: dict
    ):
        """Test dashboard loading performance with large datasets."""
        
        # Measure dashboard stats endpoint performance
        start_time = time.time()
        
        response = await async_client.get(
            "/api/v1/admin/dashboard/stats",
            headers=admin_headers
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert response_time < 500  # Should respond within 500ms
        
        # Verify response contains expected data
        stats = response.json()
        assert "total_users" in stats
        assert "active_users" in stats
        assert "system_status" in stats

    async def test_user_list_pagination_performance(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: Session
    ):
        """Test user list performance with pagination."""
        
        # Create test users for performance testing
        from app.models.user import User, AdminRole
        
        users = []
        for i in range(100):
            user = User(
                email=f"perftest{i}@example.com",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                name=f"Performance Test User {i}",
                is_active=True,
                role=AdminRole.USER
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test different page sizes
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = await async_client.get(
                f"/api/v1/admin/users?limit={page_size}&offset=0",
                headers=admin_headers
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time < 1000  # Should respond within 1 second
            
            users_data = response.json()
            assert len(users_data["users"]) <= page_size
            
            print(f"Page size {page_size}: {response_time:.2f}ms")

    async def test_concurrent_api_requests(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test performance under concurrent API requests."""
        
        async def make_request(endpoint: str):
            start_time = time.time()
            response = await async_client.get(endpoint, headers=admin_headers)
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Define endpoints to test concurrently
        endpoints = [
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/users?limit=10",
            "/api/v1/admin/moderation/queue?limit=10",
            "/api/v1/admin/notifications?limit=10",
            "/api/v1/admin/project/tasks?limit=10"
        ]
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            tasks = []
            for i in range(concurrency):
                endpoint = endpoints[i % len(endpoints)]
                tasks.append(make_request(endpoint))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = (end_time - start_time) * 1000
            
            # All requests should succeed
            for result in results:
                assert result["status_code"] == 200
                assert result["response_time"] < 2000  # Individual request < 2s
            
            # Total time should be reasonable for concurrent execution
            assert total_time < 5000  # Total time < 5s
            
            avg_response_time = sum(r["response_time"] for r in results) / len(results)
            print(f"Concurrency {concurrency}: Total {total_time:.2f}ms, Avg {avg_response_time:.2f}ms")

    async def test_large_dataset_operations(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: Session
    ):
        """Test performance with large datasets."""
        
        # Create large number of notifications for testing
        from app.models.notification import Notification
        
        notifications = []
        for i in range(500):
            notification = Notification(
                type="info",
                title=f"Performance Test Notification {i}",
                message=f"This is test notification number {i} for performance testing",
                priority="medium",
                channels=["web"]
            )
            notifications.append(notification)
        
        # Measure bulk insert performance
        start_time = time.time()
        db_session.add_all(notifications)
        db_session.commit()
        insert_time = (time.time() - start_time) * 1000
        
        assert insert_time < 5000  # Bulk insert should complete within 5 seconds
        print(f"Bulk insert of 500 notifications: {insert_time:.2f}ms")
        
        # Measure query performance with large dataset
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/notifications?limit=100",
            headers=admin_headers
        )
        query_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert query_time < 1000  # Query should complete within 1 second
        print(f"Query 100 notifications from 500: {query_time:.2f}ms")
        
        # Test search performance
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/notifications?search=performance&limit=50",
            headers=admin_headers
        )
        search_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert search_time < 1500  # Search should complete within 1.5 seconds
        print(f"Search in 500 notifications: {search_time:.2f}ms")

    async def test_real_time_updates_performance(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        mock_websocket
    ):
        """Test performance of real-time update system."""
        
        # Simulate rapid WebSocket updates
        update_count = 100
        
        start_time = time.time()
        
        for i in range(update_count):
            # Simulate dashboard update
            await mock_websocket.broadcast_dashboard_update({
                "active_users": 100 + i,
                "timestamp": time.time()
            })
            
            # Simulate notification
            if i % 10 == 0:  # Every 10th update
                await mock_websocket.send_notification(
                    user_id=1,
                    notification={
                        "type": "info",
                        "message": f"Update {i}",
                        "timestamp": time.time()
                    }
                )
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Should handle 100 updates quickly
        assert total_time < 1000  # Within 1 second
        
        avg_time_per_update = total_time / update_count
        assert avg_time_per_update < 10  # Less than 10ms per update
        
        print(f"100 WebSocket updates: {total_time:.2f}ms ({avg_time_per_update:.2f}ms per update)")

    async def test_backup_operations_performance(
        self,
        async_client: AsyncClient,
        super_admin_headers: dict,
        mock_backup_service
    ):
        """Test backup operations performance."""
        
        # Test backup creation performance
        backup_data = {
            "backup_type": "manual",
            "components": ["database", "files"],
            "description": "Performance test backup"
        }
        
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/admin/backup/create",
            json=backup_data,
            headers=super_admin_headers
        )
        creation_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 202  # Accepted for async processing
        assert creation_time < 500  # Backup initiation should be fast
        
        backup_id = response.json()["backup_id"]
        
        # Test backup status check performance
        start_time = time.time()
        response = await async_client.get(
            f"/api/v1/admin/backup/{backup_id}",
            headers=super_admin_headers
        )
        status_check_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert status_check_time < 200  # Status check should be very fast
        
        print(f"Backup creation: {creation_time:.2f}ms, Status check: {status_check_time:.2f}ms")

    async def test_moderation_queue_performance(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: Session
    ):
        """Test moderation queue performance with many messages."""
        
        # Create many messages for moderation
        from app.models.moderation import ModerationMessage, ModerationStatus
        
        messages = []
        for i in range(200):
            message = ModerationMessage(
                content=f"Performance test message {i}",
                ai_response=f"AI response for message {i}",
                user_id=1,
                status=ModerationStatus.PENDING,
                priority="medium" if i % 2 == 0 else "high"
            )
            messages.append(message)
        
        db_session.add_all(messages)
        db_session.commit()
        
        # Test queue loading performance
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/moderation/queue?limit=50",
            headers=admin_headers
        )
        queue_load_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert queue_load_time < 800  # Should load within 800ms
        
        # Test filtering performance
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/moderation/queue?priority=high&limit=25",
            headers=admin_headers
        )
        filter_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert filter_time < 600  # Filtering should be fast
        
        print(f"Queue load: {queue_load_time:.2f}ms, Filter: {filter_time:.2f}ms")

    async def test_analytics_computation_performance(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: Session
    ):
        """Test analytics computation performance."""
        
        # Create test data for analytics
        from app.models.user import User, AdminRole
        from datetime import datetime, timedelta
        
        # Create users with different creation dates
        users = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(100):
            user = User(
                email=f"analytics{i}@example.com",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                name=f"Analytics User {i}",
                is_active=True,
                role=AdminRole.USER,
                created_at=base_date + timedelta(days=i % 30)
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test dashboard analytics performance
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard?period=30d",
            headers=admin_headers
        )
        analytics_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert analytics_time < 2000  # Analytics should compute within 2 seconds
        
        # Test user growth analytics
        start_time = time.time()
        response = await async_client.get(
            "/api/v1/admin/analytics/users/growth?period=30d",
            headers=admin_headers
        )
        growth_analytics_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert growth_analytics_time < 1500  # Growth analytics within 1.5 seconds
        
        print(f"Dashboard analytics: {analytics_time:.2f}ms, Growth analytics: {growth_analytics_time:.2f}ms")

    @pytest.mark.slow
    async def test_stress_test_admin_operations(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Stress test admin operations under high load."""
        
        # Define operations to stress test
        operations = [
            lambda: async_client.get("/api/v1/admin/dashboard/stats", headers=admin_headers),
            lambda: async_client.get("/api/v1/admin/users?limit=10", headers=admin_headers),
            lambda: async_client.get("/api/v1/admin/moderation/queue?limit=10", headers=admin_headers),
            lambda: async_client.get("/api/v1/admin/notifications?limit=10", headers=admin_headers),
        ]
        
        # Run stress test
        total_requests = 200
        concurrent_requests = 20
        
        async def run_operation_batch():
            tasks = []
            for _ in range(concurrent_requests):
                operation = operations[_ % len(operations)]
                tasks.append(operation())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        start_time = time.time()
        
        # Run batches of concurrent requests
        all_results = []
        for batch in range(total_requests // concurrent_requests):
            batch_results = await run_operation_batch()
            all_results.extend(batch_results)
            
            # Small delay between batches to simulate realistic load
            await asyncio.sleep(0.1)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Analyze results
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        for result in all_results:
            if isinstance(result, Exception):
                failed_requests += 1
            else:
                successful_requests += 1
        
        success_rate = (successful_requests / total_requests) * 100
        
        # Assertions for stress test
        assert success_rate >= 95  # At least 95% success rate
        assert total_time < 30000  # Complete within 30 seconds
        
        avg_time_per_request = total_time / total_requests
        assert avg_time_per_request < 150  # Average less than 150ms per request
        
        print(f"Stress test: {total_requests} requests in {total_time:.2f}ms")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Average time per request: {avg_time_per_request:.2f}ms")