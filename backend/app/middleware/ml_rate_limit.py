"""
Rate Limiting Middleware for ML Endpoints
Интегрирует MLRateLimiter с FastAPI endpoints
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Dict, Any, Optional
import re
from datetime import datetime

from ..core.ml_rate_limiter import MLRateLimiter, EndpointType

logger = logging.getLogger(__name__)


class MLRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for ML endpoint rate limiting"""
    
    def __init__(self, app, rate_limiter: Optional[MLRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or MLRateLimiter()
        
        # Endpoint pattern matching
        self.endpoint_patterns = {
            EndpointType.CHAT_INFERENCE: [
                r'/api/v1/chat/.*',
                r'/api/v1/generate',
                r'/api/v1/vistral/.*'  # Переименовано с saiga
            ],
            EndpointType.RAG_SEARCH: [
                r'/api/v1/rag/.*',
                r'/api/v1/search',
                r'/api/v1/documents/search'
            ],
            EndpointType.EMBEDDING_GENERATION: [
                r'/api/v1/embeddings/.*',
                r'/api/v1/vectorize'
            ],
            EndpointType.LORA_TRAINING: [
                r'/api/v1/lora/training/.*',
                r'/api/v1/fine-tune'
            ],
            EndpointType.BULK_PROCESSING: [
                r'/api/v1/bulk/.*',
                r'/api/v1/batch/.*'
            ]
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for endpoint_type, patterns in self.endpoint_patterns.items():
            self.compiled_patterns[endpoint_type] = [
                re.compile(pattern) for pattern in patterns
            ]
        
        # Excluded paths (no rate limiting)
        self.excluded_paths = {
            '/health', '/ready', '/metrics', '/docs', '/openapi.json',
            '/api/v1/auth/login', '/api/v1/auth/register'
        }
    
    def _get_endpoint_type(self, path: str) -> Optional[EndpointType]:
        """Determine endpoint type from request path"""
        if path in self.excluded_paths:
            return None
        
        for endpoint_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(path):
                    return endpoint_type
        
        return None
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """Extract user ID and tier from request"""
        user_info = {
            "user_id": "anonymous",
            "user_tier": "basic",
            "api_key": None
        }
        
        # Try to get user from JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # This would integrate with your actual JWT handling
                # For now, we'll use a simple extraction
                token = auth_header[7:]
                # user_info = decode_jwt_token(token)
                user_info["user_id"] = f"user_{hash(token) % 10000}"
            except Exception:
                pass
        
        # Try to get from API key
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if api_key:
            user_info["api_key"] = api_key
            user_info["user_id"] = f"api_{hash(api_key) % 10000}"
            
            # Determine tier from API key (simplified)
            if "premium" in api_key.lower():
                user_info["user_tier"] = "premium"
            elif "enterprise" in api_key.lower():
                user_info["user_tier"] = "enterprise"
            elif "admin" in api_key.lower():
                user_info["user_tier"] = "admin"
        
        # Fallback to IP-based identification
        if user_info["user_id"] == "anonymous":
            client_ip = request.client.host if request.client else "unknown"
            user_info["user_id"] = f"ip_{hash(client_ip) % 10000}"
        
        return user_info
    
    def _estimate_request_tokens(self, request: Request, endpoint_type: EndpointType) -> int:
        """Estimate token usage for the request"""
        if endpoint_type == EndpointType.CHAT_INFERENCE:
            # Try to estimate from request body
            try:
                content_length = int(request.headers.get("content-length", "0"))
                # Rough estimate: 1 token per 4 characters
                return max(1, content_length // 4)
            except:
                return 100  # Default estimate
        
        elif endpoint_type == EndpointType.RAG_SEARCH:
            query_length = len(request.query_params.get("query", ""))
            return max(1, query_length // 4)
        
        elif endpoint_type == EndpointType.EMBEDDING_GENERATION:
            return 50  # Default embedding request cost
        
        else:
            return 1  # Default for other endpoint types
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        start_time = time.time()
        
        # Determine endpoint type
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        if endpoint_type is None:
            # No rate limiting for this endpoint
            return await call_next(request)
        
        # Extract user information
        user_info = self._extract_user_info(request)
        user_id = user_info["user_id"]
        user_tier = user_info["user_tier"]
        
        # Estimate request cost
        request_tokens = self._estimate_request_tokens(request, endpoint_type)
        
        # Check rate limits
        allowed, limit_info = await self.rate_limiter.check_rate_limit(
            user_id=user_id,
            endpoint_type=endpoint_type,
            user_tier=user_tier,
            request_tokens=request_tokens
        )
        
        if not allowed:
            # Rate limit exceeded
            wait_time = limit_info.get("wait_time", 60)
            blocked_by = limit_info.get("blocked_by", "Rate limit exceeded")
            
            logger.warning(
                f"🚫 Rate limit exceeded for {user_id} on {endpoint_type.value}: {blocked_by}"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": blocked_by,
                    "details": {
                        "user_id": user_id,
                        "endpoint_type": endpoint_type.value,
                        "wait_time_seconds": wait_time,
                        "retry_after": int(wait_time),
                        "limits_checked": limit_info.get("limits_checked", []),
                        "user_tier": user_tier
                    },
                    "timestamp": datetime.now().isoformat()
                },
                headers={
                    "Retry-After": str(int(wait_time)),
                    "X-RateLimit-Limit": str(limit_info.get("limit_value", "unknown")),
                    "X-RateLimit-Remaining": str(max(0, int(limit_info.get("tokens_available", 0)))),
                    "X-RateLimit-Reset": str(int(time.time() + wait_time))
                }
            )
        
        # Proceed with request
        try:
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            response.headers["X-RateLimit-UserTier"] = user_tier
            response.headers["X-RateLimit-EndpointType"] = endpoint_type.value
            response.headers["X-RateLimit-RequestTokens"] = str(request_tokens)
            
            # Log successful request
            duration = time.time() - start_time
            logger.info(
                f"✅ {endpoint_type.value} request for {user_id} completed in {duration:.2f}s "
                f"({request_tokens} tokens)"
            )
            
            return response
            
        except Exception as e:
            # Log failed request
            duration = time.time() - start_time
            logger.error(
                f"❌ {endpoint_type.value} request for {user_id} failed after {duration:.2f}s: {e}"
            )
            raise
    
    def get_rate_limiter(self) -> MLRateLimiter:
        """Get the rate limiter instance"""
        return self.rate_limiter


class RateLimitDependency:
    """FastAPI dependency for rate limiting"""
    
    def __init__(self, endpoint_type: EndpointType, request_tokens: int = 1):
        self.endpoint_type = endpoint_type
        self.request_tokens = request_tokens
    
    async def __call__(self, request: Request, rate_limiter: MLRateLimiter = None):
        """Check rate limits as a dependency"""
        if rate_limiter is None:
            # Get rate limiter from middleware or create new instance
            rate_limiter = MLRateLimiter()
        
        # Extract user info
        middleware = MLRateLimitMiddleware(None)
        user_info = middleware._extract_user_info(request)
        
        # Check rate limits
        allowed, limit_info = await rate_limiter.check_rate_limit(
            user_id=user_info["user_id"],
            endpoint_type=self.endpoint_type,
            user_tier=user_info["user_tier"],
            request_tokens=self.request_tokens
        )
        
        if not allowed:
            from fastapi import HTTPException
            wait_time = limit_info.get("wait_time", 60)
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": limit_info.get("blocked_by", "Rate limit exceeded"),
                    "wait_time_seconds": wait_time,
                    "user_tier": user_info["user_tier"]
                },
                headers={
                    "Retry-After": str(int(wait_time))
                }
            )
        
        return limit_info


# Convenience functions for common rate limits
def chat_rate_limit(request_tokens: int = 100):
    """Rate limit for chat endpoints"""
    return RateLimitDependency(EndpointType.CHAT_INFERENCE, request_tokens)

def rag_rate_limit():
    """Rate limit for RAG search endpoints"""
    return RateLimitDependency(EndpointType.RAG_SEARCH, 1)

def embedding_rate_limit():
    """Rate limit for embedding generation"""
    return RateLimitDependency(EndpointType.EMBEDDING_GENERATION, 1)

def training_rate_limit():
    """Rate limit for training endpoints"""
    return RateLimitDependency(EndpointType.LORA_TRAINING, 1)