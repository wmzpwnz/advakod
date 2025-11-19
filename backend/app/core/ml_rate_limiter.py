"""
Advanced Rate Limiting for ML Endpoints
Реализует M-02: Token-bucket rate limiting для ML endpoints с GPU queue management
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import redis
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class LimitType(Enum):
    """Types of rate limits"""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    GPU_CONCURRENCY = "gpu_concurrency"
    INFERENCE_QUEUE = "inference_queue"


class EndpointType(Enum):
    """ML Endpoint types with different resource requirements"""
    CHAT_INFERENCE = "chat_inference"
    RAG_SEARCH = "rag_search"
    EMBEDDING_GENERATION = "embedding_generation"
    LORA_TRAINING = "lora_training"
    MODEL_FINE_TUNE = "model_fine_tune"
    BULK_PROCESSING = "bulk_processing"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit: int
    window_seconds: int
    limit_type: LimitType
    burst_allowance: int = 0
    description: str = ""


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)
    
    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get wait time until tokens are available"""
        self.refill()
        if self.tokens >= tokens:
            return 0.0
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


@dataclass
class UserLimitState:
    """State for a user's rate limits"""
    user_id: str
    buckets: Dict[str, TokenBucket] = field(default_factory=dict)
    request_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_seen: float = field(default_factory=time.time)
    
    def update_last_seen(self):
        self.last_seen = time.time()


class MLRateLimiter:
    """Advanced rate limiter for ML endpoints"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_state: Dict[str, UserLimitState] = {}
        self.gpu_queue = asyncio.Queue(maxsize=10)  # GPU inference queue
        self.active_gpu_jobs = 0
        self.max_gpu_concurrent = 3
        
        # Rate limit configurations by endpoint type
        self.rate_limits = {
            EndpointType.CHAT_INFERENCE: [
                RateLimit(30, 60, LimitType.REQUESTS_PER_MINUTE, burst_allowance=10, 
                         description="Chat inference requests per minute"),
                RateLimit(500, 3600, LimitType.REQUESTS_PER_HOUR, burst_allowance=50,
                         description="Chat inference requests per hour"),
                RateLimit(100000, 60, LimitType.TOKENS_PER_MINUTE, burst_allowance=20000,
                         description="Token generation per minute")
            ],
            EndpointType.RAG_SEARCH: [
                RateLimit(60, 60, LimitType.REQUESTS_PER_MINUTE, burst_allowance=20,
                         description="RAG search requests per minute"),
                RateLimit(1000, 3600, LimitType.REQUESTS_PER_HOUR, burst_allowance=100,
                         description="RAG search requests per hour")
            ],
            EndpointType.EMBEDDING_GENERATION: [
                RateLimit(120, 60, LimitType.REQUESTS_PER_MINUTE, burst_allowance=30,
                         description="Embedding generation per minute"),
                RateLimit(2000, 3600, LimitType.REQUESTS_PER_HOUR, burst_allowance=200,
                         description="Embedding generation per hour")
            ],
            EndpointType.LORA_TRAINING: [
                RateLimit(5, 3600, LimitType.REQUESTS_PER_HOUR, burst_allowance=2,
                         description="LoRA training jobs per hour"),
                RateLimit(1, 1, LimitType.GPU_CONCURRENCY, burst_allowance=0,
                         description="Concurrent training jobs")
            ],
            EndpointType.BULK_PROCESSING: [
                RateLimit(10, 3600, LimitType.REQUESTS_PER_HOUR, burst_allowance=3,
                         description="Bulk processing jobs per hour"),
                RateLimit(2, 1, LimitType.GPU_CONCURRENCY, burst_allowance=0,
                         description="Concurrent bulk jobs")
            ]
        }
        
        # VIP user configurations
        self.vip_multipliers = {
            "premium": 5.0,
            "enterprise": 10.0,
            "admin": 100.0
        }
        
        # Cleanup task
        self._cleanup_task = None
        # Отложим запуск до инициализации event loop
        self._cleanup_started = False
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_started:
            return
        
        try:
            async def cleanup_loop():
                while True:
                    await asyncio.sleep(300)  # 5 minutes
                    self._cleanup_old_states()
            
            self._cleanup_task = asyncio.create_task(cleanup_loop())
            self._cleanup_started = True
        except RuntimeError:
            # Event loop не запущен, отложим до запуска
            pass
    
    async def initialize_cleanup(self):
        """Инициализировать cleanup task после запуска event loop"""
        if not self._cleanup_started:
            self._start_cleanup_task()
    
    def _cleanup_old_states(self):
        """Remove old user states to prevent memory leaks"""
        now = time.time()
        cutoff = now - 3600  # 1 hour
        
        to_remove = [
            user_id for user_id, state in self.local_state.items()
            if state.last_seen < cutoff
        ]
        
        for user_id in to_remove:
            del self.local_state[user_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old rate limit states")
    
    def get_user_limits(self, user_id: str, user_tier: str = "basic") -> Dict[str, RateLimit]:
        """Get rate limits for user with tier-based multipliers"""
        multiplier = self.vip_multipliers.get(user_tier, 1.0)
        
        user_limits = {}
        for endpoint_type, limits in self.rate_limits.items():
            user_limits[endpoint_type.value] = []
            for limit in limits:
                user_limit = RateLimit(
                    limit=int(limit.limit * multiplier),
                    window_seconds=limit.window_seconds,
                    limit_type=limit.limit_type,
                    burst_allowance=int(limit.burst_allowance * multiplier),
                    description=f"{limit.description} (tier: {user_tier})"
                )
                user_limits[endpoint_type.value].append(user_limit)
        
        return user_limits
    
    def _get_user_state(self, user_id: str) -> UserLimitState:
        """Get or create user rate limit state"""
        if user_id not in self.local_state:
            self.local_state[user_id] = UserLimitState(user_id=user_id)
        
        state = self.local_state[user_id]
        state.update_last_seen()
        return state
    
    def _create_bucket_key(self, endpoint_type: EndpointType, limit: RateLimit) -> str:
        """Create unique bucket key"""
        return f"{endpoint_type.value}:{limit.limit_type.value}:{limit.window_seconds}"
    
    def _get_or_create_bucket(self, user_state: UserLimitState, endpoint_type: EndpointType, 
                             limit: RateLimit, user_tier: str = "basic") -> TokenBucket:
        """Get or create token bucket for user and limit"""
        bucket_key = self._create_bucket_key(endpoint_type, limit)
        
        if bucket_key not in user_state.buckets:
            multiplier = self.vip_multipliers.get(user_tier, 1.0)
            capacity = int(limit.limit * multiplier) + int(limit.burst_allowance * multiplier)
            refill_rate = (limit.limit * multiplier) / limit.window_seconds
            
            user_state.buckets[bucket_key] = TokenBucket(
                capacity=capacity,
                tokens=capacity,  # Start with full bucket
                refill_rate=refill_rate
            )
        
        return user_state.buckets[bucket_key]
    
    async def check_rate_limit(self, user_id: str, endpoint_type: EndpointType, 
                              user_tier: str = "basic", request_tokens: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Returns:
            (allowed, limit_info)
        """
        user_state = self._get_user_state(user_id)
        
        # Get applicable rate limits
        limits = self.rate_limits.get(endpoint_type, [])
        
        limit_info = {
            "user_id": user_id,
            "endpoint_type": endpoint_type.value,
            "user_tier": user_tier,
            "timestamp": time.time(),
            "limits_checked": [],
            "wait_time": 0.0
        }
        
        max_wait_time = 0.0
        
        for limit in limits:
            bucket = self._get_or_create_bucket(user_state, endpoint_type, limit, user_tier)
            
            # Calculate tokens needed based on limit type
            tokens_needed = request_tokens if limit.limit_type == LimitType.TOKENS_PER_MINUTE else 1
            
            can_proceed = bucket.consume(tokens_needed)
            wait_time = bucket.get_wait_time(tokens_needed) if not can_proceed else 0.0
            
            limit_status = {
                "limit_type": limit.limit_type.value,
                "limit_value": limit.limit,
                "window_seconds": limit.window_seconds,
                "tokens_available": bucket.tokens,
                "tokens_needed": tokens_needed,
                "allowed": can_proceed,
                "wait_time": wait_time,
                "description": limit.description
            }
            
            limit_info["limits_checked"].append(limit_status)
            
            if not can_proceed:
                max_wait_time = max(max_wait_time, wait_time)
                limit_info["wait_time"] = max_wait_time
                limit_info["blocked_by"] = limit.description
                
                # Log rate limit hit
                logger.warning(f"🚫 Rate limit hit for user {user_id}: {limit.description}")
                
                return False, limit_info
        
        # Check GPU concurrency limits
        if endpoint_type in [EndpointType.LORA_TRAINING, EndpointType.BULK_PROCESSING]:
            if self.active_gpu_jobs >= self.max_gpu_concurrent:
                queue_wait_time = self.gpu_queue.qsize() * 30  # Estimate wait time
                limit_info["wait_time"] = queue_wait_time
                limit_info["blocked_by"] = "GPU concurrency limit"
                limit_info["gpu_queue_size"] = self.gpu_queue.qsize()
                
                logger.warning(f"🔥 GPU concurrency limit hit for user {user_id}")
                return False, limit_info
        
        # Record successful request
        user_state.request_history.append({
            "timestamp": time.time(),
            "endpoint_type": endpoint_type.value,
            "tokens": request_tokens,
            "allowed": True
        })
        
        return True, limit_info
    
    async def acquire_gpu_slot(self, user_id: str, job_id: str) -> bool:
        """Acquire GPU slot for intensive operations"""
        if self.active_gpu_jobs >= self.max_gpu_concurrent:
            try:
                await asyncio.wait_for(self.gpu_queue.put((user_id, job_id)), timeout=300)
                logger.info(f"🔥 GPU job {job_id} queued for user {user_id}")
                return False  # Queued, not yet acquired
            except asyncio.TimeoutError:
                logger.error(f"🔥 GPU queue timeout for job {job_id}")
                return False
        
        self.active_gpu_jobs += 1
        logger.info(f"🔥 GPU slot acquired for job {job_id} (active: {self.active_gpu_jobs})")
        return True
    
    async def release_gpu_slot(self, job_id: str):
        """Release GPU slot and process queue"""
        if self.active_gpu_jobs > 0:
            self.active_gpu_jobs -= 1
            logger.info(f"🔥 GPU slot released for job {job_id} (active: {self.active_gpu_jobs})")
        
        # Process next in queue
        if not self.gpu_queue.empty() and self.active_gpu_jobs < self.max_gpu_concurrent:
            try:
                user_id, queued_job_id = await self.gpu_queue.get()
                self.active_gpu_jobs += 1
                logger.info(f"🔥 GPU slot assigned to queued job {queued_job_id}")
                
                # Notify the waiting job (this would need additional coordination mechanism)
                # For now, we'll just log it
            except Exception as e:
                logger.error(f"Error processing GPU queue: {e}")
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get detailed stats for a user"""
        user_state = self.local_state.get(user_id)
        if not user_state:
            return {"user_id": user_id, "no_activity": True}
        
        stats = {
            "user_id": user_id,
            "last_seen": user_state.last_seen,
            "buckets": {},
            "recent_requests": list(user_state.request_history)[-10:]  # Last 10 requests
        }
        
        for bucket_key, bucket in user_state.buckets.items():
            bucket.refill()  # Update tokens
            stats["buckets"][bucket_key] = {
                "capacity": bucket.capacity,
                "current_tokens": bucket.tokens,
                "refill_rate": bucket.refill_rate,
                "utilization": (bucket.capacity - bucket.tokens) / bucket.capacity
            }
        
        return stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide rate limiting stats"""
        return {
            "total_users": len(self.local_state),
            "active_gpu_jobs": self.active_gpu_jobs,
            "max_gpu_concurrent": self.max_gpu_concurrent,
            "gpu_queue_size": self.gpu_queue.qsize(),
            "rate_limit_configurations": {
                endpoint.value: [
                    {
                        "limit": limit.limit,
                        "window_seconds": limit.window_seconds,
                        "type": limit.limit_type.value,
                        "description": limit.description
                    }
                    for limit in limits
                ]
                for endpoint, limits in self.rate_limits.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Dependency for FastAPI
def get_rate_limiter() -> MLRateLimiter:
    """Get rate limiter instance"""
    if not hasattr(get_rate_limiter, '_instance'):
        get_rate_limiter._instance = MLRateLimiter()
    return get_rate_limiter._instance


# Rate limit decorator
def rate_limit(endpoint_type: EndpointType, request_tokens: int = 1):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and user info from FastAPI dependencies
            # This would need to be integrated with the actual FastAPI app
            pass
        return wrapper
    return decorator