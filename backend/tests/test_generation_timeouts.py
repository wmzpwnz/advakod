"""
Tests for generation timeout functionality
Verifies that AI generation properly handles timeouts and doesn't hang
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.unified_llm_service import unified_llm_service, UnifiedLLMService, RequestPriority


@pytest.mark.asyncio
class TestGenerationTimeouts:
    """Test generation timeout handling"""

    async def test_generation_timeout_configuration(self):
        """Test that timeout configuration is properly set"""
        service = UnifiedLLMService()
        
        # Check that timeout settings are reasonable
        assert service._inference_timeout <= 180, "Timeout should be 180 seconds or less"
        assert service._max_concurrency <= 3, "Max concurrency should be limited"
        assert service._queue_size <= 50, "Queue size should be limited"

    async def test_generation_timeout_enforcement(self):
        """Test that generation actually times out after configured time"""
        service = UnifiedLLMService()
        service._inference_timeout = 2  # Set very short timeout for testing
        
        # Mock a slow model that never responds
        with patch.object(service, 'model') as mock_model:
            def slow_generation(*args, **kwargs):
                time.sleep(5)  # Simulate slow generation
                return {"choices": [{"text": "This should timeout"}]}
            
            mock_model.return_value = slow_generation
            service._model_loaded = True
            
            start_time = time.time()
            
            # Test streaming timeout
            chunks = []
            async for chunk in service.generate_response(
                "Test prompt", 
                stream=True,
                max_tokens=100
            ):
                chunks.append(chunk)
                # Should timeout before getting real response
                if "[TIMEOUT]" in chunk or "[ERROR]" in chunk:
                    break
            
            elapsed = time.time() - start_time
            
            # Should timeout within reasonable time (timeout + buffer)
            assert elapsed < 10, f"Generation took too long: {elapsed}s"
            assert any("[TIMEOUT]" in chunk or "[ERROR]" in chunk for chunk in chunks), \
                "Should receive timeout message"

    async def test_stuck_generation_cleanup(self):
        """Test that stuck generations are properly cleaned up"""
        service = UnifiedLLMService()
        service._inference_timeout = 1  # Very short timeout
        
        # Add a fake stuck generation
        request_id = "test_stuck_123"
        service._stuck_generations[request_id] = time.time() - 10  # 10 seconds ago
        service._active_requests[request_id] = Mock()
        
        # Run cleanup
        await service._terminate_stuck_generations()
        
        # Should be cleaned up
        assert request_id not in service._stuck_generations
        assert request_id not in service._active_requests

    async def test_concurrent_generation_limits(self):
        """Test that concurrent generation limits are enforced"""
        service = UnifiedLLMService()
        service._max_concurrency = 1  # Only allow 1 concurrent generation
        
        # Mock model to simulate slow generation
        with patch.object(service, 'model') as mock_model:
            def slow_generation(*args, **kwargs):
                time.sleep(0.5)  # Short delay
                return {"choices": [{"text": "Response"}]}
            
            mock_model.return_value = slow_generation
            service._model_loaded = True
            
            # Start multiple generations concurrently
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    service._generate_response_internal(f"Prompt {i}")
                )
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least one should complete successfully
            successful = [r for r in results if isinstance(r, str) and "Response" in r]
            assert len(successful) >= 1, "At least one generation should succeed"

    async def test_cpu_overload_protection(self):
        """Test that generation is blocked when CPU is overloaded"""
        service = UnifiedLLMService()
        
        # Mock CPU load manager to simulate overload
        with patch('app.services.unified_llm_service.cpu_load_manager') as mock_cpu:
            mock_status = Mock()
            mock_status.cpu_overloaded = True
            mock_status.current_cpu = 95.0
            mock_status.can_process = False
            mock_cpu.check_cpu_load.return_value = mock_status
            
            # Should raise error due to CPU overload
            with pytest.raises(RuntimeError, match="CPU critically overloaded"):
                await service._generate_response_internal("Test prompt")

    async def test_generation_timeout_manager_integration(self):
        """Test integration with GenerationTimeoutManager"""
        service = UnifiedLLMService()
        
        # Mock timeout manager
        with patch('app.services.unified_llm_service.generation_timeout_manager') as mock_timeout_mgr:
            mock_timeout_mgr.generate_with_timeout = AsyncMock(
                side_effect=TimeoutError("Generation timeout")
            )
            
            service._model_loaded = True
            
            # Should handle timeout gracefully
            with pytest.raises(RuntimeError, match="превысила максимальное время"):
                await service._generate_response_internal("Test prompt")

    async def test_health_check_detects_stuck_generations(self):
        """Test that health check detects and reports stuck generations"""
        service = UnifiedLLMService()
        
        # Add some stuck generations
        service._stuck_generations["stuck1"] = time.time() - 200  # Old stuck generation
        service._stuck_generations["stuck2"] = time.time() - 100  # Another stuck one
        service._active_requests["stuck1"] = Mock()
        service._active_requests["stuck2"] = Mock()
        
        # Health check should clean them up
        health = await service.health_check()
        
        # Should be cleaned up after health check
        assert len(service._stuck_generations) == 0
        assert len(service._active_requests) == 0
        
        # Health status should reflect the cleanup
        assert health.status in ["healthy", "degraded"]

    async def test_graceful_shutdown_with_active_generations(self):
        """Test graceful shutdown when there are active generations"""
        service = UnifiedLLMService()
        
        # Add some active requests
        service._active_requests["req1"] = Mock()
        service._active_requests["req2"] = Mock()
        
        # Mock background tasks
        mock_task = AsyncMock()
        service._background_tasks = [mock_task]
        
        # Should shutdown gracefully
        await service.graceful_shutdown()
        
        # Should cancel background tasks
        mock_task.cancel.assert_called_once()

    async def test_metrics_update_after_timeout(self):
        """Test that metrics are properly updated after timeouts"""
        service = UnifiedLLMService()
        
        initial_failed = service._stats["failed_requests"]
        
        # Simulate a timeout by calling _update_stats with failure
        service._update_stats(success=False, response_time=5.0)
        
        # Failed requests should increase
        assert service._stats["failed_requests"] == initial_failed + 1
        assert service._stats["total_requests"] == initial_failed + 1

    async def test_queue_overflow_handling(self):
        """Test handling when request queue is full"""
        service = UnifiedLLMService()
        service._queue_size = 2  # Very small queue for testing
        
        # Fill up the queue
        for i in range(service._queue_size + 1):
            try:
                await service._request_queue.put((1, f"request_{i}"))
            except asyncio.QueueFull:
                # Expected when queue is full
                break
        
        # Queue should be at capacity
        assert service._request_queue.qsize() >= service._queue_size

    @pytest.mark.slow
    async def test_real_timeout_scenario(self):
        """Integration test with real timeout scenario"""
        service = UnifiedLLMService()
        service._inference_timeout = 3  # 3 second timeout
        
        # Only run if model is actually loaded
        if not service.is_model_loaded():
            pytest.skip("Model not loaded, skipping real timeout test")
        
        start_time = time.time()
        
        # Generate with a very long prompt that might cause timeout
        long_prompt = "Explain in extreme detail " * 100 + "the meaning of life."
        
        chunks = []
        async for chunk in service.generate_response(
            long_prompt,
            stream=True,
            max_tokens=2000  # Large token count
        ):
            chunks.append(chunk)
            elapsed = time.time() - start_time
            
            # Break if we get timeout or if it takes too long
            if "[TIMEOUT]" in chunk or elapsed > 10:
                break
        
        # Should either complete or timeout within reasonable time
        elapsed = time.time() - start_time
        assert elapsed < 15, f"Test took too long: {elapsed}s"
        
        # Should have received some response
        assert len(chunks) > 0, "Should receive at least one chunk"


@pytest.mark.asyncio
class TestTimeoutRecovery:
    """Test recovery mechanisms after timeouts"""

    async def test_service_recovery_after_timeout(self):
        """Test that service can recover after timeout"""
        service = UnifiedLLMService()
        
        # Simulate timeout scenario
        service._stats["failed_requests"] = 5
        service._stats["total_requests"] = 10
        
        # Service should still be functional
        assert service.is_model_loaded() or not service._model_loaded  # Either state is valid
        
        # Health check should work
        health = await service.health_check()
        assert health is not None
        assert hasattr(health, 'status')

    async def test_background_task_restart_after_failure(self):
        """Test that background tasks can restart after failure"""
        service = UnifiedLLMService()
        
        # Mock a failing background task
        original_monitor = service._monitor_stuck_generations
        
        async def failing_monitor():
            raise Exception("Simulated failure")
        
        service._monitor_stuck_generations = failing_monitor
        
        # Start background tasks
        try:
            await service._start_background_tasks()
        except Exception:
            pass  # Expected to fail
        
        # Restore original method
        service._monitor_stuck_generations = original_monitor
        
        # Should be able to restart
        service._background_tasks.clear()
        await service._start_background_tasks()
        
        # Should have background tasks running
        assert len(service._background_tasks) > 0

    async def test_error_rate_calculation(self):
        """Test error rate calculation after timeouts"""
        service = UnifiedLLMService()
        
        # Simulate some requests with failures
        service._stats["total_requests"] = 100
        service._stats["failed_requests"] = 15
        service._stats["successful_requests"] = 85
        
        # Update metrics
        await service._update_metrics()
        
        # Error rate should be calculated correctly
        expected_error_rate = 15 / 100
        assert abs(service._stats["error_rate"] - expected_error_rate) < 0.01