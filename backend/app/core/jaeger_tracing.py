"""
Jaeger distributed tracing integration for Admin Panel
Provides comprehensive request tracing and performance monitoring
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
import logging

try:
    from jaeger_client import Config
    from jaeger_client.reporter import CompositeReporter
    from jaeger_client.sampler import ConstSampler
    from opentracing import tracer, Span
    from opentracing.ext import tags
    from opentracing.propagation import Format
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    tracer = None
    Span = None

from fastapi import Request, Response
from app.core.config import settings

logger = logging.getLogger(__name__)

class JaegerTracing:
    """Jaeger tracing integration for admin panel"""
    
    def __init__(self):
        self.tracer = None
        self.enabled = False
        self._initialize_tracer()
    
    def _initialize_tracer(self):
        """Initialize Jaeger tracer"""
        if not JAEGER_AVAILABLE:
            logger.warning("Jaeger client not available. Install with: pip install jaeger-client")
            return
        
        # Configuration from environment
        jaeger_host = os.getenv("JAEGER_AGENT_HOST", "localhost")
        jaeger_port = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
        service_name = os.getenv("JAEGER_SERVICE_NAME", "advakod-admin-panel")
        
        # Skip if Jaeger is disabled
        if os.getenv("JAEGER_DISABLED", "false").lower() == "true":
            logger.info("Jaeger tracing disabled by configuration")
            return
        
        try:
            config = Config(
                config={
                    'sampler': {
                        'type': 'const',
                        'param': 1,  # Sample all requests in development
                    },
                    'local_agent': {
                        'reporting_host': jaeger_host,
                        'reporting_port': jaeger_port,
                    },
                    'logging': True,
                },
                service_name=service_name,
                validate=True,
            )
            
            self.tracer = config.initialize_tracer()
            self.enabled = True
            logger.info(f"Jaeger tracing initialized for service: {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jaeger tracer: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if tracing is enabled"""
        return self.enabled and self.tracer is not None
    
    @contextmanager
    def trace_operation(self, operation_name: str, tags_dict: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations"""
        if not self.is_enabled():
            yield None
            return
        
        span = self.tracer.start_span(operation_name)
        
        try:
            # Add tags
            if tags_dict:
                for key, value in tags_dict.items():
                    span.set_tag(key, value)
            
            yield span
            
        except Exception as e:
            span.set_tag(tags.ERROR, True)
            span.log_kv({
                'event': 'error',
                'error.object': e,
                'error.kind': type(e).__name__,
                'message': str(e)
            })
            raise
        finally:
            span.finish()
    
    def trace_http_request(self, request: Request, response: Response, 
                          duration: float, user_role: str = "unknown"):
        """Trace HTTP request"""
        if not self.is_enabled():
            return
        
        operation_name = f"{request.method} {request.url.path}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                # HTTP tags
                span.set_tag(tags.HTTP_METHOD, request.method)
                span.set_tag(tags.HTTP_URL, str(request.url))
                span.set_tag(tags.HTTP_STATUS_CODE, response.status_code)
                span.set_tag("http.duration_ms", duration * 1000)
                
                # Admin panel specific tags
                span.set_tag("admin.user_role", user_role)
                span.set_tag("admin.module", self._extract_module_from_path(request.url.path))
                
                # Client information
                if request.client:
                    span.set_tag("client.ip", request.client.host)
                
                user_agent = request.headers.get("user-agent")
                if user_agent:
                    span.set_tag("client.user_agent", user_agent)
                
                # Error handling
                if response.status_code >= 400:
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({
                        'event': 'http_error',
                        'status_code': response.status_code,
                        'path': request.url.path
                    })
    
    def trace_database_operation(self, operation: str, table: str, 
                               duration: float, success: bool = True):
        """Trace database operation"""
        if not self.is_enabled():
            return
        
        operation_name = f"db.{operation}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                span.set_tag(tags.DATABASE_TYPE, "postgresql")
                span.set_tag(tags.DATABASE_STATEMENT, operation)
                span.set_tag("db.table", table)
                span.set_tag("db.duration_ms", duration * 1000)
                
                if not success:
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({
                        'event': 'db_error',
                        'operation': operation,
                        'table': table
                    })
    
    def trace_cache_operation(self, operation: str, key: str, hit: bool, 
                            duration: float):
        """Trace cache operation"""
        if not self.is_enabled():
            return
        
        operation_name = f"cache.{operation}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                span.set_tag("cache.operation", operation)
                span.set_tag("cache.key", key)
                span.set_tag("cache.hit", hit)
                span.set_tag("cache.duration_ms", duration * 1000)
    
    def trace_notification_operation(self, channel: str, notification_type: str, 
                                   recipient_count: int, duration: float, 
                                   success: bool = True):
        """Trace notification operation"""
        if not self.is_enabled():
            return
        
        operation_name = f"notification.{channel}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                span.set_tag("notification.channel", channel)
                span.set_tag("notification.type", notification_type)
                span.set_tag("notification.recipient_count", recipient_count)
                span.set_tag("notification.duration_ms", duration * 1000)
                
                if not success:
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({
                        'event': 'notification_error',
                        'channel': channel,
                        'type': notification_type
                    })
    
    def trace_analytics_query(self, query_type: str, complexity: str, 
                            duration: float, result_count: int, 
                            success: bool = True):
        """Trace analytics query"""
        if not self.is_enabled():
            return
        
        operation_name = f"analytics.{query_type}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                span.set_tag("analytics.query_type", query_type)
                span.set_tag("analytics.complexity", complexity)
                span.set_tag("analytics.duration_ms", duration * 1000)
                span.set_tag("analytics.result_count", result_count)
                
                if not success:
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({
                        'event': 'analytics_error',
                        'query_type': query_type,
                        'complexity': complexity
                    })
    
    def trace_backup_operation(self, operation_type: str, backup_type: str, 
                             duration: float, size_bytes: int, 
                             success: bool = True):
        """Trace backup operation"""
        if not self.is_enabled():
            return
        
        operation_name = f"backup.{operation_type}"
        
        with self.trace_operation(operation_name) as span:
            if span:
                span.set_tag("backup.operation", operation_type)
                span.set_tag("backup.type", backup_type)
                span.set_tag("backup.duration_ms", duration * 1000)
                span.set_tag("backup.size_bytes", size_bytes)
                
                if not success:
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({
                        'event': 'backup_error',
                        'operation': operation_type,
                        'type': backup_type
                    })
    
    def _extract_module_from_path(self, path: str) -> str:
        """Extract admin module from request path"""
        path_parts = path.strip('/').split('/')
        
        # Admin API paths: /api/v1/admin/{module}
        if len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[2] == 'admin':
            return path_parts[3]
        
        # Direct admin paths: /admin/{module}
        if len(path_parts) >= 2 and path_parts[0] == 'admin':
            return path_parts[1]
        
        return "unknown"
    
    def create_child_span(self, parent_span, operation_name: str, 
                         tags_dict: Optional[Dict[str, Any]] = None):
        """Create a child span"""
        if not self.is_enabled() or not parent_span:
            return None
        
        child_span = self.tracer.start_span(
            operation_name,
            child_of=parent_span
        )
        
        if tags_dict:
            for key, value in tags_dict.items():
                child_span.set_tag(key, value)
        
        return child_span
    
    def inject_span_context(self, span, headers: Dict[str, str]):
        """Inject span context into headers for downstream services"""
        if not self.is_enabled() or not span:
            return
        
        self.tracer.inject(
            span_context=span.context,
            format=Format.HTTP_HEADERS,
            carrier=headers
        )
    
    def extract_span_context(self, headers: Dict[str, str]):
        """Extract span context from headers"""
        if not self.is_enabled():
            return None
        
        try:
            return self.tracer.extract(
                format=Format.HTTP_HEADERS,
                carrier=headers
            )
        except Exception as e:
            logger.debug(f"Failed to extract span context: {e}")
            return None
    
    def close(self):
        """Close the tracer"""
        if self.tracer:
            self.tracer.close()
            logger.info("Jaeger tracer closed")

def trace_function(operation_name: Optional[str] = None, 
                  tags: Optional[Dict[str, Any]] = None):
    """Decorator for tracing functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with jaeger_tracing.trace_operation(op_name, tags) as span:
                try:
                    if span:
                        span.set_tag("function.name", func.__name__)
                        span.set_tag("function.module", func.__module__)
                    
                    result = await func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    if span:
                        span.set_tag(tags.ERROR, True)
                        span.log_kv({
                            'event': 'function_error',
                            'error.object': e,
                            'error.kind': type(e).__name__,
                            'message': str(e)
                        })
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with jaeger_tracing.trace_operation(op_name, tags) as span:
                try:
                    if span:
                        span.set_tag("function.name", func.__name__)
                        span.set_tag("function.module", func.__module__)
                    
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    if span:
                        span.set_tag(tags.ERROR, True)
                        span.log_kv({
                            'event': 'function_error',
                            'error.object': e,
                            'error.kind': type(e).__name__,
                            'message': str(e)
                        })
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Global instance
jaeger_tracing = JaegerTracing()