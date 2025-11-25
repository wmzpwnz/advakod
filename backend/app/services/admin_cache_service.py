"""
Admin Panel Cache Service
Implements intelligent caching for heavy admin panel queries and operations
"""

import json
import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.cache import cache_service
from app.core.admin_panel_metrics import admin_panel_metrics
from app.core.jaeger_tracing import jaeger_tracing, trace_function

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    LFU = "lfu"  # Least Frequently Used
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"

@dataclass
class CacheConfig:
    """Cache configuration"""
    strategy: CacheStrategy = CacheStrategy.TTL
    ttl_seconds: int = 300  # 5 minutes default
    max_size: int = 1000
    enable_compression: bool = True
    enable_encryption: bool = False
    invalidation_tags: List[str] = None

class AdminCacheService:
    """Comprehensive caching service for admin panel operations"""
    
    def __init__(self):
        self.cache_configs = {
            # Dashboard metrics - short TTL for real-time feel
            "dashboard_metrics": CacheConfig(ttl_seconds=30, max_size=50),
            
            # User analytics - medium TTL
            "user_analytics": CacheConfig(ttl_seconds=300, max_size=200),
            
            # RBAC data - longer TTL, invalidate on changes
            "rbac_data": CacheConfig(ttl_seconds=1800, max_size=100, 
                                   invalidation_tags=["rbac_change"]),
            
            # Moderation queue - short TTL
            "moderation_queue": CacheConfig(ttl_seconds=60, max_size=100),
            
            # Marketing analytics - longer TTL
            "marketing_analytics": CacheConfig(ttl_seconds=900, max_size=300),
            
            # Project data - medium TTL
            "project_data": CacheConfig(ttl_seconds=600, max_size=200),
            
            # Notification templates - long TTL
            "notification_templates": CacheConfig(ttl_seconds=3600, max_size=50),
            
            # Analytics queries - variable TTL based on complexity
            "analytics_queries": CacheConfig(ttl_seconds=1800, max_size=500),
            
            # Backup metadata - long TTL
            "backup_metadata": CacheConfig(ttl_seconds=7200, max_size=100),
            
            # System settings - very long TTL
            "system_settings": CacheConfig(ttl_seconds=14400, max_size=50)
        }
        
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "errors": 0
        }
        
        self.invalidation_tags = {}  # tag -> set of cache keys
    
    def _generate_cache_key(self, category: str, identifier: str, 
                          params: Dict[str, Any] = None) -> str:
        """Generate a consistent cache key"""
        key_parts = [category, identifier]
        
        if params:
            # Sort params for consistent key generation
            sorted_params = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    def _get_cache_config(self, category: str) -> CacheConfig:
        """Get cache configuration for category"""
        return self.cache_configs.get(category, CacheConfig())
    
    @trace_function("admin_cache_get")
    async def get(self, category: str, identifier: str, 
                  params: Dict[str, Any] = None) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_cache_key(category, identifier, params)
        
        try:
            # Record cache operation for tracing
            start_time = asyncio.get_event_loop().time()
            
            cached_data = await cache_service.get(cache_key)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            if cached_data is not None:
                self.cache_stats["hits"] += 1
                admin_panel_metrics.record_cache_operation(category, "admin_panel", True)
                
                jaeger_tracing.trace_cache_operation("get", cache_key, True, duration)
                
                logger.debug(f"Cache hit for {cache_key}")
                return json.loads(cached_data) if isinstance(cached_data, str) else cached_data
            else:
                self.cache_stats["misses"] += 1
                admin_panel_metrics.record_cache_operation(category, "admin_panel", False)
                
                jaeger_tracing.trace_cache_operation("get", cache_key, False, duration)
                
                logger.debug(f"Cache miss for {cache_key}")
                return None
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache get error for {cache_key}: {e}")
            return None
    
    @trace_function("admin_cache_set")
    async def set(self, category: str, identifier: str, value: Any, 
                  params: Dict[str, Any] = None, ttl_override: int = None) -> bool:
        """Set value in cache"""
        cache_key = self._generate_cache_key(category, identifier, params)
        config = self._get_cache_config(category)
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = value
            
            # Use TTL override or config default
            ttl = ttl_override or config.ttl_seconds
            
            # Store in cache
            success = await cache_service.set(cache_key, serialized_value, ttl)
            
            duration = asyncio.get_event_loop().time() - start_time
            jaeger_tracing.trace_cache_operation("set", cache_key, success, duration)
            
            # Track invalidation tags
            if config.invalidation_tags:
                for tag in config.invalidation_tags:
                    if tag not in self.invalidation_tags:
                        self.invalidation_tags[tag] = set()
                    self.invalidation_tags[tag].add(cache_key)
            
            logger.debug(f"Cache set for {cache_key} (TTL: {ttl}s)")
            return success
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache set error for {cache_key}: {e}")
            return False
    
    @trace_function("admin_cache_invalidate")
    async def invalidate(self, category: str, identifier: str = None, 
                        params: Dict[str, Any] = None, tag: str = None) -> int:
        """Invalidate cache entries"""
        invalidated_count = 0
        
        try:
            if tag:
                # Invalidate by tag
                if tag in self.invalidation_tags:
                    keys_to_invalidate = list(self.invalidation_tags[tag])
                    for key in keys_to_invalidate:
                        if await cache_service.delete(key):
                            invalidated_count += 1
                    self.invalidation_tags[tag].clear()
            elif identifier:
                # Invalidate specific key
                cache_key = self._generate_cache_key(category, identifier, params)
                if await cache_service.delete(cache_key):
                    invalidated_count = 1
            else:
                # Invalidate all keys in category (pattern-based)
                pattern = f"{category}:*"
                keys = await cache_service.get_keys_by_pattern(pattern)
                for key in keys:
                    if await cache_service.delete(key):
                        invalidated_count += 1
            
            self.cache_stats["invalidations"] += invalidated_count
            logger.info(f"Invalidated {invalidated_count} cache entries")
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache invalidation error: {e}")
        
        return invalidated_count
    
    async def get_or_set(self, category: str, identifier: str, 
                        fetch_function: Callable, params: Dict[str, Any] = None,
                        ttl_override: int = None) -> Any:
        """Get from cache or fetch and set if not found"""
        # Try to get from cache first
        cached_value = await self.get(category, identifier, params)
        if cached_value is not None:
            return cached_value
        
        # Fetch fresh data
        try:
            fresh_value = await fetch_function()
            
            # Cache the fresh data
            await self.set(category, identifier, fresh_value, params, ttl_override)
            
            return fresh_value
            
        except Exception as e:
            logger.error(f"Error fetching data for cache {category}:{identifier}: {e}")
            raise
    
    async def warm_cache(self, category: str, warm_function: Callable) -> int:
        """Warm up cache with pre-computed data"""
        try:
            warm_data = await warm_function()
            warmed_count = 0
            
            for identifier, value in warm_data.items():
                if await self.set(category, identifier, value):
                    warmed_count += 1
            
            logger.info(f"Warmed {warmed_count} cache entries for {category}")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Cache warming error for {category}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_operations = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_operations * 100) if total_operations > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_operations": total_operations,
            "active_tags": len(self.invalidation_tags),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def clear_all_cache(self) -> int:
        """Clear all admin panel cache"""
        try:
            cleared_count = 0
            for category in self.cache_configs.keys():
                count = await self.invalidate(category)
                cleared_count += count
            
            # Clear invalidation tags
            self.invalidation_tags.clear()
            
            logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

# Specific cache services for different admin modules

class DashboardCacheService:
    """Specialized caching for dashboard data"""
    
    def __init__(self, cache_service: AdminCacheService):
        self.cache = cache_service
    
    async def get_dashboard_metrics(self, user_role: str, time_range: str) -> Optional[Dict]:
        """Get cached dashboard metrics"""
        return await self.cache.get(
            "dashboard_metrics", 
            f"metrics_{user_role}",
            {"time_range": time_range}
        )
    
    async def set_dashboard_metrics(self, user_role: str, time_range: str, 
                                  metrics: Dict) -> bool:
        """Cache dashboard metrics"""
        return await self.cache.set(
            "dashboard_metrics",
            f"metrics_{user_role}",
            metrics,
            {"time_range": time_range},
            ttl_override=30  # Short TTL for real-time feel
        )

class AnalyticsCacheService:
    """Specialized caching for analytics queries"""
    
    def __init__(self, cache_service: AdminCacheService):
        self.cache = cache_service
    
    async def get_analytics_result(self, query_hash: str, params: Dict) -> Optional[Dict]:
        """Get cached analytics result"""
        return await self.cache.get("analytics_queries", query_hash, params)
    
    async def set_analytics_result(self, query_hash: str, params: Dict, 
                                 result: Dict, complexity: str = "medium") -> bool:
        """Cache analytics result with TTL based on complexity"""
        ttl_map = {
            "simple": 300,    # 5 minutes
            "medium": 1800,   # 30 minutes
            "complex": 3600   # 1 hour
        }
        
        return await self.cache.set(
            "analytics_queries",
            query_hash,
            result,
            params,
            ttl_override=ttl_map.get(complexity, 1800)
        )

class UserCacheService:
    """Specialized caching for user data"""
    
    def __init__(self, cache_service: AdminCacheService):
        self.cache = cache_service
    
    async def get_user_analytics(self, user_id: int, metric_type: str) -> Optional[Dict]:
        """Get cached user analytics"""
        return await self.cache.get(
            "user_analytics",
            f"user_{user_id}",
            {"metric_type": metric_type}
        )
    
    async def set_user_analytics(self, user_id: int, metric_type: str, 
                               analytics: Dict) -> bool:
        """Cache user analytics"""
        return await self.cache.set(
            "user_analytics",
            f"user_{user_id}",
            analytics,
            {"metric_type": metric_type}
        )
    
    async def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache for a specific user"""
        return await self.cache.invalidate("user_analytics", f"user_{user_id}")

# Global instances
admin_cache_service = AdminCacheService()
dashboard_cache = DashboardCacheService(admin_cache_service)
analytics_cache = AnalyticsCacheService(admin_cache_service)
user_cache = UserCacheService(admin_cache_service)