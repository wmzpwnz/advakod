#!/usr/bin/env python3
"""
Test script to verify Redis connection and fallback mechanism
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.cache import cache_service
from app.core.config import settings

async def test_redis_connection():
    """Test Redis connection and fallback mechanism"""
    print("🔧 Testing Redis Connection and Fallback Mechanism")
    print("=" * 60)
    
    # Initialize cache service
    print(f"📡 Redis URL: {settings.REDIS_URL}")
    cache_service.redis_url = settings.REDIS_URL
    
    print("🚀 Initializing cache service...")
    await cache_service.initialize()
    
    # Check health status
    print("\n📊 Cache Health Status:")
    health = await cache_service.health_check()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Test basic operations
    print("\n🧪 Testing Cache Operations:")
    
    # Test SET operation
    test_key = "test:redis:connection"
    test_value = {"message": "Hello Redis!", "timestamp": "2025-10-30"}
    
    print(f"  Setting key '{test_key}'...")
    success = await cache_service.set(test_key, test_value, ttl=60)
    print(f"  SET result: {success}")
    
    # Test GET operation
    print(f"  Getting key '{test_key}'...")
    retrieved_value = await cache_service.get(test_key)
    print(f"  GET result: {retrieved_value}")
    
    # Test EXISTS operation
    print(f"  Checking if key '{test_key}' exists...")
    exists = await cache_service.exists(test_key)
    print(f"  EXISTS result: {exists}")
    
    # Test DELETE operation
    print(f"  Deleting key '{test_key}'...")
    deleted = await cache_service.delete(test_key)
    print(f"  DELETE result: {deleted}")
    
    # Verify deletion
    print(f"  Verifying deletion...")
    exists_after = await cache_service.exists(test_key)
    print(f"  EXISTS after delete: {exists_after}")
    
    # Get cache statistics
    print("\n📈 Cache Statistics:")
    stats = await cache_service.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    # Test fallback mechanism by simulating Redis failure
    print("\n🔄 Testing Fallback Mechanism:")
    if cache_service.redis_client and cache_service._initialized:
        print("  Redis is connected, testing fallback by closing connection...")
        try:
            await cache_service.redis_client.close()
            cache_service._initialized = False
            print("  Redis connection closed")
            
            # Test operations with fallback
            fallback_key = "test:fallback:key"
            fallback_value = {"fallback": True, "mode": "in-memory"}
            
            print(f"  Setting key '{fallback_key}' with fallback...")
            success = await cache_service.set(fallback_key, fallback_value, ttl=60)
            print(f"  Fallback SET result: {success}")
            
            print(f"  Getting key '{fallback_key}' with fallback...")
            retrieved = await cache_service.get(fallback_key)
            print(f"  Fallback GET result: {retrieved}")
            
        except Exception as e:
            print(f"  Error during fallback test: {e}")
    else:
        print("  Redis not connected, already using fallback mode")
        
        # Test in-memory operations
        fallback_key = "test:memory:key"
        fallback_value = {"memory": True, "mode": "in-memory-only"}
        
        print(f"  Setting key '{fallback_key}' in memory...")
        success = await cache_service.set(fallback_key, fallback_value, ttl=60)
        print(f"  Memory SET result: {success}")
        
        print(f"  Getting key '{fallback_key}' from memory...")
        retrieved = await cache_service.get(fallback_key)
        print(f"  Memory GET result: {retrieved}")
    
    # Final health check
    print("\n🏁 Final Health Check:")
    final_health = await cache_service.health_check()
    for key, value in final_health.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    await cache_service.close()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())