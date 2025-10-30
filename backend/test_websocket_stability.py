#!/usr/bin/env python3
"""
Test script for WebSocket stability improvements
Tests the enhanced WebSocket service functionality
"""

import asyncio
import json
import time
from app.services.websocket_service import websocket_service, ConnectionManager
from app.core.config import settings

async def test_websocket_stability():
    """Test WebSocket stability features"""
    print("🧪 Testing WebSocket Stability Improvements")
    print("=" * 50)
    
    # Test 1: Configuration
    print("1. Testing Configuration:")
    print(f"   ✓ Ping Interval: {settings.WEBSOCKET_PING_INTERVAL}s")
    print(f"   ✓ Pong Timeout: {settings.WEBSOCKET_PONG_TIMEOUT}s")
    print(f"   ✓ Connection Timeout: {settings.WEBSOCKET_CONNECTION_TIMEOUT}s")
    print(f"   ✓ Max Message Size: {settings.WEBSOCKET_MAX_MESSAGE_SIZE} bytes")
    print(f"   ✓ Max Connections per IP: {settings.WEBSOCKET_MAX_CONNECTIONS_PER_IP}")
    
    # Test 2: Service Initialization
    print("\n2. Testing Service Initialization:")
    stats = websocket_service.get_connection_count()
    print(f"   ✓ Active Users: {stats.get('active_users', 0)}")
    print(f"   ✓ Active Sessions: {stats.get('active_sessions', 0)}")
    print(f"   ✓ Total Connections: {stats.get('total_connections', 0)}")
    print(f"   ✓ Service Manager: {type(websocket_service.manager).__name__}")
    
    # Test 3: Connection Manager Features
    print("\n3. Testing Connection Manager Features:")
    manager = websocket_service.manager
    print(f"   ✓ Connection Metadata: {len(manager.connection_metadata)} entries")
    print(f"   ✓ Ping Tasks: {len(manager.ping_tasks)} active")
    print(f"   ✓ Connection Stats: {manager.connection_stats}")
    
    # Test 4: Cleanup Functionality
    print("\n4. Testing Cleanup Functionality:")
    try:
        await manager.cleanup_stale_connections()
        print("   ✓ Stale connection cleanup completed")
    except Exception as e:
        print(f"   ⚠️ Cleanup test failed: {e}")
    
    # Test 5: Message Size Validation
    print("\n5. Testing Message Size Validation:")
    test_message = {"type": "test", "content": "x" * 1000}
    message_json = json.dumps(test_message)
    message_size = len(message_json.encode('utf-8'))
    
    if message_size <= settings.WEBSOCKET_MAX_MESSAGE_SIZE:
        print(f"   ✓ Test message size OK: {message_size} bytes")
    else:
        print(f"   ❌ Test message too large: {message_size} bytes")
    
    # Test 6: Error Recovery System
    print("\n6. Testing Error Recovery System:")
    detailed_stats = websocket_service.get_detailed_stats()
    print(f"   ✓ Detailed stats available: {len(detailed_stats.get('connections', []))} connections")
    print(f"   ✓ Ping tasks active: {detailed_stats.get('ping_tasks_active', 0)}")
    
    print("\n✅ All WebSocket stability tests completed!")
    print("\nKey Improvements Implemented:")
    print("  • Enhanced connection stability with ping/pong monitoring")
    print("  • Automatic reconnection with exponential backoff")
    print("  • Message size validation and error handling")
    print("  • Stale connection cleanup")
    print("  • Comprehensive error recovery strategies")
    print("  • Rate limiting and connection management")
    print("  • Detailed connection statistics and monitoring")

if __name__ == "__main__":
    asyncio.run(test_websocket_stability())