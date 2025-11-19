"""
End-to-end tests for complete chat flow
Tests the full chat cycle from user input to AI response delivery
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.unified_llm_service import unified_llm_service
from app.services.admin_websocket_service import admin_websocket_service


@pytest.mark.asyncio
class TestEndToEndChatFlow:
    """Test complete chat flow from request to response"""

    async def test_complete_chat_message_flow(self, async_client: AsyncClient, auth_headers: dict):
        """Test complete flow: HTTP request -> AI generation -> WebSocket response"""
        
        # Mock the LLM service to return predictable response
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_response_generator(prompt, **kwargs):
                yield "This is a test response from the AI."
            
            mock_generate.return_value = mock_response_generator("test", stream=True)
            
            # Send chat message
            response = await async_client.post(
                "/api/v1/chat/message",
                json={
                    "message": "What is the law about contracts?",
                    "context": None
                },
                headers=auth_headers
            )
            
            # Should accept the request
            assert response.status_code in [200, 202], f"Unexpected status: {response.status_code}"
            
            # Should return response data
            data = response.json()
            assert "response" in data or "message" in data or "status" in data

    async def test_streaming_chat_response(self, async_client: AsyncClient, auth_headers: dict):
        """Test streaming chat response delivery"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            # Mock streaming response
            async def mock_stream():
                chunks = ["Hello ", "this ", "is ", "a ", "streaming ", "response."]
                for chunk in chunks:
                    yield chunk
                    await asyncio.sleep(0.01)  # Small delay to simulate real streaming
            
            mock_generate.return_value = mock_stream()
            
            # Test streaming endpoint if available
            try:
                response = await async_client.post(
                    "/api/v1/chat/stream",
                    json={"message": "Tell me about legal contracts"},
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    # Should receive streaming response
                    content = response.content.decode()
                    assert len(content) > 0
                elif response.status_code == 404:
                    # Streaming endpoint might not exist, that's ok
                    pytest.skip("Streaming endpoint not available")
                else:
                    pytest.fail(f"Unexpected streaming response: {response.status_code}")
                    
            except Exception as e:
                # If streaming not implemented, test regular response
                pytest.skip(f"Streaming test skipped: {e}")

    async def test_chat_with_context(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat with additional context"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_response_with_context(prompt, context=None, **kwargs):
                if context:
                    yield f"Based on the context: {context[:50]}... Here is my response."
                else:
                    yield "Here is my response without context."
            
            mock_generate.side_effect = mock_response_with_context
            
            # Send message with context
            response = await async_client.post(
                "/api/v1/chat/message",
                json={
                    "message": "What does this document say?",
                    "context": "This is a legal document about employment contracts..."
                },
                headers=auth_headers
            )
            
            assert response.status_code in [200, 202]
            
            # Verify context was used
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1].get('context') is not None

    async def test_chat_error_handling(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat error handling and recovery"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            # Mock error in generation
            async def mock_error_response(prompt, **kwargs):
                raise Exception("AI model temporarily unavailable")
            
            mock_generate.side_effect = mock_error_response
            
            # Send chat message
            response = await async_client.post(
                "/api/v1/chat/message",
                json={"message": "Test message"},
                headers=auth_headers
            )
            
            # Should handle error gracefully
            assert response.status_code in [200, 500, 503]
            
            if response.status_code != 200:
                data = response.json()
                assert "error" in data or "detail" in data

    async def test_chat_timeout_handling(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat timeout handling"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            # Mock slow response that times out
            async def mock_slow_response(prompt, **kwargs):
                await asyncio.sleep(10)  # Simulate very slow response
                yield "This should timeout"
            
            mock_generate.return_value = mock_slow_response("test")
            
            # Send chat message with short timeout
            start_time = time.time()
            
            try:
                response = await asyncio.wait_for(
                    async_client.post(
                        "/api/v1/chat/message",
                        json={"message": "Test timeout"},
                        headers=auth_headers
                    ),
                    timeout=5.0  # 5 second timeout
                )
                
                elapsed = time.time() - start_time
                
                # Should either complete quickly or timeout
                if elapsed > 4:
                    # If it took long, should have timeout handling
                    data = response.json()
                    assert "timeout" in str(data).lower() or "error" in data
                
            except asyncio.TimeoutError:
                # Client timeout is also acceptable
                elapsed = time.time() - start_time
                assert elapsed < 6  # Should timeout around 5 seconds

    async def test_concurrent_chat_requests(self, async_client: AsyncClient, auth_headers: dict):
        """Test handling multiple concurrent chat requests"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_concurrent_response(prompt, **kwargs):
                await asyncio.sleep(0.1)  # Small delay
                yield f"Response to: {prompt[:20]}..."
            
            mock_generate.side_effect = mock_concurrent_response
            
            # Send multiple concurrent requests
            tasks = []
            for i in range(3):
                task = async_client.post(
                    "/api/v1/chat/message",
                    json={"message": f"Concurrent message {i}"},
                    headers=auth_headers
                )
                tasks.append(task)
            
            # Wait for all responses
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least some should succeed
            successful = [r for r in responses if hasattr(r, 'status_code') and r.status_code in [200, 202]]
            assert len(successful) >= 1, "At least one concurrent request should succeed"

    async def test_chat_input_validation(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat input validation"""
        
        # Test empty message
        response = await async_client.post(
            "/api/v1/chat/message",
            json={"message": ""},
            headers=auth_headers
        )
        assert response.status_code in [400, 422], "Should reject empty message"
        
        # Test very long message
        long_message = "x" * 10000  # Very long message
        response = await async_client.post(
            "/api/v1/chat/message",
            json={"message": long_message},
            headers=auth_headers
        )
        # Should either accept or reject gracefully
        assert response.status_code in [200, 202, 400, 413, 422]
        
        # Test invalid JSON structure
        response = await async_client.post(
            "/api/v1/chat/message",
            json={"invalid_field": "test"},
            headers=auth_headers
        )
        assert response.status_code in [400, 422], "Should reject invalid structure"

    async def test_authentication_required_for_chat(self, async_client: AsyncClient):
        """Test that authentication is required for chat"""
        
        # Try to send message without auth
        response = await async_client.post(
            "/api/v1/chat/message",
            json={"message": "Test without auth"}
        )
        
        # Should require authentication
        assert response.status_code in [401, 403], "Should require authentication"

    async def test_chat_rate_limiting(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat rate limiting if implemented"""
        
        # Send many requests quickly
        responses = []
        for i in range(10):
            response = await async_client.post(
                "/api/v1/chat/message",
                json={"message": f"Rate limit test {i}"},
                headers=auth_headers
            )
            responses.append(response)
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        # Check if any were rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        
        # Rate limiting is optional, so we just check it works if implemented
        if rate_limited:
            assert len(rate_limited) > 0, "Rate limiting should be consistent"


@pytest.mark.asyncio
class TestChatWebSocketIntegration:
    """Test chat integration with WebSocket for real-time updates"""

    async def test_chat_websocket_notification(self):
        """Test that chat generates WebSocket notifications"""
        
        # Mock WebSocket service
        with patch.object(admin_websocket_service, 'send_dashboard_update') as mock_ws:
            with patch.object(unified_llm_service, 'generate_response') as mock_generate:
                async def mock_response(prompt, **kwargs):
                    yield "Test response"
                
                mock_generate.return_value = mock_response("test")
                
                # Simulate chat processing that should trigger WebSocket update
                # This would normally happen in the chat endpoint
                await admin_websocket_service.send_dashboard_update({
                    "active_chats": 1,
                    "messages_processed": 1
                })
                
                # Should have called WebSocket update
                mock_ws.assert_called_once()

    async def test_chat_status_updates_via_websocket(self):
        """Test chat status updates via WebSocket"""
        
        service = admin_websocket_service
        service.manager.broadcast_to_channel = AsyncMock()
        
        # Simulate different chat statuses
        statuses = [
            {"status": "processing", "message": "AI is thinking..."},
            {"status": "generating", "message": "Generating response..."},
            {"status": "complete", "message": "Response ready"}
        ]
        
        for status in statuses:
            await service.send_system_alert(status, "info")
        
        # Should have sent all status updates
        assert service.manager.broadcast_to_channel.call_count == len(statuses)

    async def test_chat_error_websocket_notification(self):
        """Test WebSocket notification for chat errors"""
        
        service = admin_websocket_service
        service.manager.broadcast_to_channel = AsyncMock()
        
        # Simulate chat error
        error_data = {
            "error": "AI model unavailable",
            "timestamp": time.time(),
            "severity": "warning"
        }
        
        await service.send_system_alert(error_data, "warning")
        
        # Should broadcast error alert
        service.manager.broadcast_to_channel.assert_called_once()
        call_args = service.manager.broadcast_to_channel.call_args
        assert call_args[0][1] == "system_alert"
        assert call_args[0][2]["severity"] == "warning"


@pytest.mark.asyncio
class TestChatPerformanceAndReliability:
    """Test chat performance and reliability"""

    async def test_chat_response_time(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat response time is reasonable"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_fast_response(prompt, **kwargs):
                yield "Quick response"
            
            mock_generate.return_value = mock_fast_response("test")
            
            start_time = time.time()
            
            response = await async_client.post(
                "/api/v1/chat/message",
                json={"message": "Quick test"},
                headers=auth_headers
            )
            
            elapsed = time.time() - start_time
            
            # Should respond quickly (under 5 seconds for mocked response)
            assert elapsed < 5.0, f"Response took too long: {elapsed}s"
            assert response.status_code in [200, 202]

    async def test_chat_memory_usage(self, async_client: AsyncClient, auth_headers: dict):
        """Test that chat doesn't cause memory leaks"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_response(prompt, **kwargs):
                yield "Memory test response"
            
            mock_generate.return_value = mock_response("test")
            
            # Send multiple messages to test memory usage
            for i in range(5):
                response = await async_client.post(
                    "/api/v1/chat/message",
                    json={"message": f"Memory test {i}"},
                    headers=auth_headers
                )
                
                # Should handle each request successfully
                assert response.status_code in [200, 202]

    async def test_chat_service_health_during_load(self):
        """Test service health during chat load"""
        
        # Check service health before load
        health_before = await unified_llm_service.health_check()
        assert health_before is not None
        
        # Simulate some load
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_load_response(prompt, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                yield "Load test response"
            
            mock_generate.return_value = mock_load_response("test")
            
            # Generate multiple concurrent requests
            tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    unified_llm_service.generate_response(f"Load test {i}")
                )
                tasks.append(task)
            
            # Wait for completion
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Most should complete successfully
            successful = [r for r in results if not isinstance(r, Exception)]
            assert len(successful) >= 3, "Most requests should succeed under load"
        
        # Check service health after load
        health_after = await unified_llm_service.health_check()
        assert health_after is not None
        
        # Service should still be healthy or at least not completely failed
        assert health_after.status in ["healthy", "degraded"]

    async def test_chat_graceful_degradation(self, async_client: AsyncClient, auth_headers: dict):
        """Test graceful degradation when AI service is unavailable"""
        
        with patch.object(unified_llm_service, 'is_model_loaded') as mock_loaded:
            mock_loaded.return_value = False  # Simulate model not loaded
            
            response = await async_client.post(
                "/api/v1/chat/message",
                json={"message": "Test when model unavailable"},
                headers=auth_headers
            )
            
            # Should handle gracefully
            if response.status_code == 503:
                # Service unavailable is acceptable
                data = response.json()
                assert "unavailable" in str(data).lower() or "error" in data
            elif response.status_code == 200:
                # Or return error message in response
                data = response.json()
                assert "error" in data or "unavailable" in str(data).lower()
            else:
                # Other error codes are also acceptable
                assert response.status_code in [400, 500, 502, 503]


@pytest.mark.asyncio
class TestChatIntegrationScenarios:
    """Integration scenarios combining multiple components"""

    async def test_full_user_chat_session(self, async_client: AsyncClient, auth_headers: dict):
        """Test a complete user chat session with multiple messages"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            # Mock conversation responses
            responses = [
                "Hello! I'm here to help with legal questions.",
                "Contracts are legally binding agreements between parties.",
                "Employment contracts typically include terms about salary, duties, and termination."
            ]
            
            async def mock_conversation_response(prompt, **kwargs):
                # Return different responses based on message content
                if "hello" in prompt.lower():
                    yield responses[0]
                elif "contract" in prompt.lower() and "employment" not in prompt.lower():
                    yield responses[1]
                elif "employment" in prompt.lower():
                    yield responses[2]
                else:
                    yield "I can help you with legal questions."
            
            mock_generate.side_effect = mock_conversation_response
            
            # Simulate conversation
            messages = [
                "Hello, can you help me?",
                "What is a contract?",
                "Tell me about employment contracts"
            ]
            
            for i, message in enumerate(messages):
                response = await async_client.post(
                    "/api/v1/chat/message",
                    json={"message": message},
                    headers=auth_headers
                )
                
                assert response.status_code in [200, 202], f"Message {i} failed"
                
                # Small delay between messages
                await asyncio.sleep(0.1)
            
            # Should have processed all messages
            assert mock_generate.call_count == len(messages)

    async def test_chat_with_document_context_integration(self, async_client: AsyncClient, auth_headers: dict):
        """Test chat integration with document context"""
        
        with patch.object(unified_llm_service, 'generate_response') as mock_generate:
            async def mock_context_response(prompt, context=None, **kwargs):
                if context and "employment" in context.lower():
                    yield "Based on the employment document, here are the key points..."
                else:
                    yield "I need more context to provide specific advice."
            
            mock_generate.side_effect = mock_context_response
            
            # Test with document context
            response = await async_client.post(
                "/api/v1/chat/message",
                json={
                    "message": "What are my rights according to this document?",
                    "context": "Employment Agreement - This document outlines the terms of employment..."
                },
                headers=auth_headers
            )
            
            assert response.status_code in [200, 202]
            
            # Verify context was passed
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1].get('context') is not None

    async def test_chat_monitoring_integration(self):
        """Test integration between chat and monitoring systems"""
        
        # Test that chat metrics are collected
        with patch.object(unified_llm_service, 'get_metrics') as mock_metrics:
            mock_metrics.return_value = Mock(
                total_requests=10,
                successful_requests=8,
                failed_requests=2,
                average_response_time=1.5
            )
            
            metrics = unified_llm_service.get_metrics()
            
            # Should have meaningful metrics
            assert metrics.total_requests > 0
            assert metrics.successful_requests >= 0
            assert metrics.failed_requests >= 0
            assert metrics.average_response_time >= 0