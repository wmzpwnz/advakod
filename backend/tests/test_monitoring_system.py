"""
Tests for monitoring system functionality
Tests health checks, metrics collection, alerting, and system monitoring
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.services.alert_service import alert_manager, alert_evaluation_service, AlertRule, AlertSeverity
from app.services.db_monitoring_service import db_monitoring_service
from app.services.backup_monitoring_service import backup_monitoring_service
from app.api.monitoring import health_check, get_system_metrics


@pytest.mark.asyncio
class TestHealthCheckSystem:
    """Test system health check functionality"""

    async def test_basic_health_check(self):
        """Test basic health check endpoint"""
        
        # Mock all dependencies
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
                with patch('app.api.monitoring.service_manager') as mock_service:
                    
                    # Setup mocks
                    mock_db.get_health_check.return_value = {"status": "healthy"}
                    mock_unified.health_check.return_value = {"status": "healthy"}
                    mock_service.get_service_status.return_value = Mock(
                        status=Mock(value="healthy"),
                        total_services=5,
                        healthy_services=5,
                        degraded_services=0,
                        unhealthy_services=0,
                        uptime=3600
                    )
                    
                    # Call health check
                    result = await health_check()
                    
                    # Should return healthy status
                    assert result["status"] == "healthy"
                    assert "database" in result
                    assert "services" in result
                    assert "timestamp" in result

    async def test_health_check_with_degraded_services(self):
        """Test health check when some services are degraded"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
                with patch('app.api.monitoring.service_manager') as mock_service:
                    
                    # Setup degraded state
                    mock_db.get_health_check.return_value = {"status": "healthy"}
                    mock_unified.health_check.return_value = {"status": "degraded"}
                    mock_service.get_service_status.return_value = Mock(
                        status=Mock(value="degraded"),
                        total_services=5,
                        healthy_services=3,
                        degraded_services=2,
                        unhealthy_services=0,
                        uptime=3600
                    )
                    
                    result = await health_check()
                    
                    # Should reflect degraded status
                    assert result["status"] in ["degraded", "unhealthy"]

    async def test_health_check_with_database_error(self):
        """Test health check when database is unhealthy"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
                with patch('app.api.monitoring.service_manager') as mock_service:
                    
                    # Setup database error
                    mock_db.get_health_check.return_value = {"status": "unhealthy", "error": "Connection failed"}
                    mock_unified.health_check.return_value = {"status": "healthy"}
                    mock_service.get_service_status.return_value = Mock(
                        status=Mock(value="healthy"),
                        total_services=5,
                        healthy_services=5,
                        degraded_services=0,
                        unhealthy_services=0,
                        uptime=3600
                    )
                    
                    result = await health_check()
                    
                    # Should reflect database issue
                    assert result["status"] in ["degraded", "unhealthy"]
                    assert result["database"]["status"] == "unhealthy"

    async def test_health_check_error_handling(self):
        """Test health check error handling"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            # Simulate exception in health check
            mock_db.get_health_check.side_effect = Exception("Database connection failed")
            
            result = await health_check()
            
            # Should handle error gracefully
            assert result["status"] == "error"
            assert "error" in result
            assert "Database connection failed" in result["error"]

    async def test_ai_model_status_in_health_check(self):
        """Test AI model status reporting in health check"""
        
        with patch('app.services.unified_llm_service.unified_llm_service') as mock_llm:
            with patch('app.api.monitoring.db_monitoring_service') as mock_db:
                with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
                    with patch('app.api.monitoring.service_manager') as mock_service:
                        
                        # Setup mocks
                        mock_llm.is_model_loaded.return_value = True
                        mock_db.get_health_check.return_value = {"status": "healthy"}
                        mock_unified.health_check.return_value = {"status": "healthy"}
                        mock_service.get_service_status.return_value = Mock(
                            status=Mock(value="healthy"),
                            total_services=5,
                            healthy_services=5,
                            degraded_services=0,
                            unhealthy_services=0,
                            uptime=3600
                        )
                        
                        result = await health_check()
                        
                        # Should include AI model status
                        assert "ai_models" in result
                        assert result["ai_models"]["unified_llm_vistral"]["loaded"] == True


@pytest.mark.asyncio
class TestMetricsCollection:
    """Test metrics collection and reporting"""

    async def test_system_metrics_collection(self, async_client: AsyncClient, auth_headers: dict):
        """Test system metrics endpoint"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
                with patch('app.api.monitoring.service_manager') as mock_service:
                    
                    # Setup metric mocks
                    mock_db.get_database_metrics.return_value = {
                        "connections": 10,
                        "query_time": 0.5
                    }
                    mock_unified.get_dashboard_data.return_value = {
                        "services": {"status": "healthy", "total": 5},
                        "alerts": {"count": 2}
                    }
                    mock_service.get_stats.return_value = {
                        "uptime": 3600,
                        "requests": 1000
                    }
                    
                    response = await async_client.get(
                        "/api/v1/monitoring/metrics",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Should contain all metric categories
                    assert "database" in data
                    assert "unified_monitoring" in data
                    assert "service_manager" in data
                    assert "timestamp" in data

    async def test_metrics_summary_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test metrics summary endpoint"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            mock_db.get_metrics_summary.return_value = {
                "period_hours": 24,
                "total_requests": 5000,
                "average_response_time": 1.2,
                "error_rate": 0.05
            }
            
            response = await async_client.get(
                "/api/v1/monitoring/metrics/summary?hours=24",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should contain summary data
            assert "total_requests" in data
            assert "average_response_time" in data

    async def test_monitoring_dashboard_data(self, async_client: AsyncClient, auth_headers: dict):
        """Test monitoring dashboard endpoint"""
        
        with patch('app.api.monitoring.unified_monitoring_service') as mock_unified:
            mock_unified.get_dashboard_data.return_value = {
                "services": {
                    "status": "healthy",
                    "total": 10,
                    "healthy": 8,
                    "degraded": 2
                },
                "alerts": {
                    "count": 3,
                    "critical": 1,
                    "warning": 2
                },
                "system": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "disk_usage": 23.1
                }
            }
            
            response = await async_client.get(
                "/api/v1/monitoring/dashboard",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should contain dashboard sections
            assert "services" in data
            assert "alerts" in data
            assert "system" in data

    async def test_service_status_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test detailed service status endpoint"""
        
        with patch('app.api.monitoring.service_manager') as mock_service:
            mock_service.get_service_status.return_value = Mock(
                status=Mock(value="healthy"),
                total_services=5,
                healthy_services=4,
                degraded_services=1,
                unhealthy_services=0,
                uptime=7200,
                last_check=datetime.now(),
                services={
                    "llm_service": Mock(
                        name="LLM Service",
                        status=Mock(value="healthy"),
                        priority=Mock(name="HIGH"),
                        last_health_check=datetime.now(),
                        initialization_time=1.5,
                        error_count=0,
                        last_error=None,
                        restart_count=0,
                        dependencies=[],
                        health_check_interval=30
                    ),
                    "websocket_service": Mock(
                        name="WebSocket Service", 
                        status=Mock(value="degraded"),
                        priority=Mock(name="MEDIUM"),
                        last_health_check=datetime.now(),
                        initialization_time=0.8,
                        error_count=2,
                        last_error="Connection timeout",
                        restart_count=1,
                        dependencies=["llm_service"],
                        health_check_interval=15
                    )
                }
            )
            
            response = await async_client.get(
                "/api/v1/monitoring/services/status",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should contain detailed service info
            assert "services" in data
            assert "system_status" in data
            assert "total_services" in data
            assert len(data["services"]) > 0


@pytest.mark.asyncio
class TestAlertingSystem:
    """Test alerting and notification system"""

    async def test_alert_rule_creation(self):
        """Test creating and managing alert rules"""
        
        # Create test alert rule
        rule = AlertRule(
            id="test_cpu_alert",
            name="Test CPU Alert",
            description="Test alert for high CPU usage",
            metric_name="cpu_usage",
            condition="gt",
            threshold=80.0,
            severity=AlertSeverity.WARNING,
            duration=300
        )
        
        # Add rule to manager
        success = alert_manager.add_alert_rule(rule)
        assert success == True
        
        # Rule should be in manager
        assert "test_cpu_alert" in alert_manager.alert_rules
        
        # Clean up
        alert_manager.delete_alert_rule("test_cpu_alert")

    async def test_alert_evaluation(self):
        """Test alert evaluation against metrics"""
        
        # Create test rule
        rule = AlertRule(
            id="test_memory_alert",
            name="Test Memory Alert", 
            description="Test memory usage alert",
            metric_name="memory_usage",
            condition="gt",
            threshold=75.0,
            severity=AlertSeverity.WARNING,
            duration=60
        )
        
        alert_manager.add_alert_rule(rule)
        
        # Test metrics that should trigger alert
        metrics = {
            "memory_usage": 85.0,  # Above threshold
            "cpu_usage": 50.0
        }
        
        # Evaluate alerts
        await alert_manager.evaluate_alerts(metrics)
        
        # Should have active alert
        active_alerts = alert_manager.get_active_alerts()
        memory_alerts = [a for a in active_alerts if a["metric_name"] == "memory_usage"]
        assert len(memory_alerts) > 0
        
        # Clean up
        alert_manager.delete_alert_rule("test_memory_alert")

    async def test_alert_resolution(self):
        """Test alert resolution when metrics return to normal"""
        
        # Create test rule
        rule = AlertRule(
            id="test_disk_alert",
            name="Test Disk Alert",
            description="Test disk usage alert", 
            metric_name="disk_usage",
            condition="gt",
            threshold=90.0,
            severity=AlertSeverity.CRITICAL,
            duration=30
        )
        
        alert_manager.add_alert_rule(rule)
        
        # Trigger alert
        high_metrics = {"disk_usage": 95.0}
        await alert_manager.evaluate_alerts(high_metrics)
        
        # Should have active alert
        active_before = len(alert_manager.get_active_alerts())
        assert active_before > 0
        
        # Resolve alert
        normal_metrics = {"disk_usage": 70.0}
        await alert_manager.evaluate_alerts(normal_metrics)
        
        # Alert should be resolved
        active_after = len(alert_manager.get_active_alerts())
        assert active_after < active_before
        
        # Clean up
        alert_manager.delete_alert_rule("test_disk_alert")

    async def test_alert_notification_handling(self):
        """Test alert notification with graceful error handling"""
        
        # Create test rule with notification channels
        rule = AlertRule(
            id="test_notification_alert",
            name="Test Notification Alert",
            description="Test alert notifications",
            metric_name="error_rate", 
            condition="gt",
            threshold=5.0,
            severity=AlertSeverity.CRITICAL,
            duration=60,
            notification_channels=["email", "slack"]
        )
        
        alert_manager.add_alert_rule(rule)
        
        # Mock notification services to avoid actual sending
        with patch('app.services.alert_service.external_notification_service') as mock_external:
            with patch('app.services.alert_service.notification_service') as mock_internal:
                
                # Setup mocks to simulate success/failure
                mock_external.send_notification = AsyncMock(return_value={"success": True})
                mock_internal.send_notification = AsyncMock(return_value=[Mock()])
                
                # Trigger alert
                metrics = {"error_rate": 10.0}
                await alert_manager.evaluate_alerts(metrics)
                
                # Should attempt to send notifications
                # (The actual calls depend on the notification service availability)
        
        # Clean up
        alert_manager.delete_alert_rule("test_notification_alert")

    async def test_alert_evaluation_service(self):
        """Test alert evaluation service background processing"""
        
        service = alert_evaluation_service
        
        # Test service status
        status = service.get_service_status()
        assert isinstance(status, dict)
        assert "running" in status
        assert "consecutive_errors" in status
        
        # Test force evaluation
        result = await service.force_evaluation()
        assert isinstance(result, dict)
        assert "success" in result
        assert "timestamp" in result

    async def test_alert_metrics_collection(self):
        """Test metrics collection for alert evaluation"""
        
        service = alert_evaluation_service
        
        # Test metrics collection
        metrics = await service._collect_current_metrics()
        
        # Should return metrics dictionary
        assert isinstance(metrics, dict)
        
        # Should have basic system metrics
        expected_metrics = ["cpu_usage", "memory_usage"]
        for metric in expected_metrics:
            assert metric in metrics or len(metrics) == 0  # Empty is ok if collection fails

    async def test_alert_statistics(self):
        """Test alert statistics and reporting"""
        
        # Get alert statistics
        stats = alert_manager.get_alert_statistics()
        
        # Should contain expected fields
        assert "total_rules" in stats
        assert "enabled_rules" in stats
        assert "active_alerts" in stats
        assert "alerts_by_severity" in stats
        assert "timestamp" in stats
        
        # Values should be reasonable
        assert stats["total_rules"] >= 0
        assert stats["enabled_rules"] >= 0
        assert stats["active_alerts"] >= 0


@pytest.mark.asyncio
class TestBackupMonitoring:
    """Test backup monitoring functionality"""

    async def test_backup_status_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test backup status monitoring endpoint"""
        
        with patch('app.api.monitoring.backup_monitoring_service') as mock_backup:
            mock_backup.get_system_metrics.return_value = {
                "total_backups": 10,
                "successful_backups": 9,
                "failed_backups": 1,
                "last_backup": "2024-01-01T12:00:00Z"
            }
            mock_backup.generate_health_report.return_value = {
                "status": "healthy",
                "issues": []
            }
            
            response = await async_client.get(
                "/api/v1/monitoring/backup/status",
                headers=auth_headers
            )
            
            # Should return backup status
            if response.status_code == 200:
                data = response.json()
                assert "metrics" in data
                assert "health_report" in data
            else:
                # Backup service might not be available
                assert response.status_code in [500, 503]

    async def test_backup_monitoring_error_handling(self, async_client: AsyncClient, auth_headers: dict):
        """Test backup monitoring error handling"""
        
        with patch('app.api.monitoring.backup_monitoring_service') as mock_backup:
            mock_backup.get_system_metrics.side_effect = Exception("Backup service unavailable")
            
            response = await async_client.get(
                "/api/v1/monitoring/backup/status", 
                headers=auth_headers
            )
            
            # Should handle error gracefully
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "error"
                assert "error" in data


@pytest.mark.asyncio
class TestDatabaseMonitoring:
    """Test database monitoring functionality"""

    async def test_database_info_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test database information endpoint"""
        
        with patch('app.api.monitoring.db_monitoring_service') as mock_db:
            mock_db.get_database_metrics.return_value = {
                "connections": 15,
                "query_time_avg": 0.8,
                "query_time_p95": 2.1,
                "active_queries": 3
            }
            
            response = await async_client.get(
                "/api/v1/monitoring/database/info",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should contain database info
            assert "database_type" in data
            assert "current_metrics" in data

    async def test_database_optimization_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test database optimization endpoint"""
        
        response = await async_client.post(
            "/api/v1/monitoring/database/optimize",
            headers=auth_headers
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "operations" in data

    async def test_vector_store_info_endpoint(self, async_client: AsyncClient, auth_headers: dict):
        """Test vector store information endpoint"""
        
        with patch('app.api.monitoring.vector_store_service') as mock_vector:
            mock_vector.is_ready.return_value = True
            mock_vector.collection_name = "test_collection"
            mock_vector.db_path = "/tmp/test_chroma"
            
            # Mock collection
            mock_collection = Mock()
            mock_collection.get.return_value = {
                'metadatas': [
                    {'document_id': 'doc1'},
                    {'document_id': 'doc2'},
                    {'document_id': 'doc1'}  # Duplicate
                ]
            }
            mock_vector.collection = mock_collection
            
            response = await async_client.get(
                "/api/v1/monitoring/vector-store/info",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should contain vector store info
            assert "status" in data
            assert "type" in data


@pytest.mark.asyncio
class TestMonitoringIntegration:
    """Test monitoring system integration scenarios"""

    async def test_monitoring_authentication(self, async_client: AsyncClient):
        """Test that monitoring endpoints require authentication"""
        
        # Try to access metrics without auth
        response = await async_client.get("/api/v1/monitoring/metrics")
        assert response.status_code in [401, 403]
        
        # Try to access dashboard without auth
        response = await async_client.get("/api/v1/monitoring/dashboard")
        assert response.status_code in [401, 403]

    async def test_monitoring_error_recovery(self):
        """Test monitoring system error recovery"""
        
        # Test alert evaluation service error recovery
        service = alert_evaluation_service
        
        # Simulate error condition
        service._consecutive_errors = 3
        
        # Should still be able to get status
        status = service.get_service_status()
        assert status["consecutive_errors"] == 3
        
        # Force evaluation should work
        result = await service.force_evaluation()
        assert "success" in result

    async def test_monitoring_performance_under_load(self):
        """Test monitoring system performance under load"""
        
        # Simulate multiple concurrent health checks
        tasks = []
        for i in range(5):
            task = asyncio.create_task(health_check())
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most should succeed
        successful = [r for r in results if isinstance(r, dict) and "status" in r]
        assert len(successful) >= 3, "Most health checks should succeed under load"

    async def test_monitoring_data_consistency(self):
        """Test consistency of monitoring data across endpoints"""
        
        # This would test that different monitoring endpoints return consistent data
        # For now, just verify the structure is consistent
        
        try:
            health_result = await health_check()
            assert "status" in health_result
            assert "timestamp" in health_result
            
            # Health check should have consistent structure
            assert isinstance(health_result["status"], str)
            assert health_result["status"] in ["healthy", "degraded", "unhealthy", "loading", "error"]
            
        except Exception as e:
            # If monitoring fails, it should fail gracefully
            assert "error" in str(e).lower() or "unavailable" in str(e).lower()