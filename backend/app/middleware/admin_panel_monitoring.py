"""
Admin Panel Monitoring Middleware
Integrates comprehensive monitoring for all admin panel operations
"""

import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.admin_panel_metrics import admin_panel_metrics
from app.core.jaeger_tracing import jaeger_tracing
from app.core.enhanced_logging import get_logger

logger = get_logger(__name__)

class AdminPanelMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive admin panel monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.admin_paths = {
            "/api/v1/admin/",
            "/api/v1/users/",
            "/api/v1/roles/",
            "/api/v1/moderation/",
            "/api/v1/analytics/",
            "/api/v1/marketing/",
            "/api/v1/project/",
            "/api/v1/notifications/",
            "/api/v1/backup/"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive monitoring"""
        # Check if this is an admin panel request
        if not self._is_admin_request(request):
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract request information
        module = self._extract_module(request.url.path)
        endpoint = self._extract_endpoint(request.url.path)
        user_role = self._extract_user_role(request)
        
        # Start Jaeger tracing is deferred until we have a real response
        
        try:
            # Process request
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            admin_panel_metrics.record_http_request(
                module=module,
                endpoint=endpoint,
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                user_role=user_role
            )
            
            # Update Jaeger trace
            jaeger_tracing.trace_http_request(request, response, duration, user_role)
            
            # Log successful request
            logger.info(
                f"Admin panel request completed",
                extra={
                    "admin_module": module,
                    "endpoint": endpoint,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration": duration,
                    "user_role": user_role
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            admin_panel_metrics.record_error(
                module=module,
                error_type=type(e).__name__,
                severity="error"
            )
            
            # Record failed request metrics
            admin_panel_metrics.record_http_request(
                module=module,
                endpoint=endpoint,
                method=request.method,
                status_code=500,
                duration=duration,
                user_role=user_role
            )
            
            # Update Jaeger trace for failed request with synthetic response
            try:
                from fastapi import Response as FastAPIResponse
                synthetic_response = FastAPIResponse(status_code=500)
                jaeger_tracing.trace_http_request(request, synthetic_response, duration, user_role)
            except Exception:
                pass

            # Log error
            logger.error(
                f"Admin panel request failed: {str(e)}",
                extra={
                    "admin_module": module,
                    "endpoint": endpoint,
                    "method": request.method,
                    "duration": duration,
                    "user_role": user_role,
                    "error": str(e)
                }
            )
            
            raise
    
    def _is_admin_request(self, request: Request) -> bool:
        """Check if request is for admin panel"""
        path = request.url.path
        return any(path.startswith(admin_path) for admin_path in self.admin_paths)
    
    def _extract_module(self, path: str) -> str:
        """Extract admin module from request path"""
        path_parts = path.strip('/').split('/')
        
        # Admin API paths: /api/v1/admin/{module} or /api/v1/{module}
        if len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[1] == 'v1':
            if path_parts[2] == 'admin' and len(path_parts) >= 4:
                return path_parts[3]
            else:
                # Direct module paths like /api/v1/users, /api/v1/roles
                module_mapping = {
                    'users': 'user_management',
                    'roles': 'rbac',
                    'moderation': 'moderation',
                    'analytics': 'analytics',
                    'marketing': 'marketing',
                    'project': 'project',
                    'notifications': 'notifications',
                    'backup': 'backup'
                }
                return module_mapping.get(path_parts[2], path_parts[2])
        
        return "unknown"
    
    def _extract_endpoint(self, path: str) -> str:
        """Extract endpoint from request path"""
        # Remove query parameters and normalize
        path = path.split('?')[0].rstrip('/')
        
        # Replace IDs with placeholders for better grouping
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', path)  # UUIDs
        
        return path
    
    def _extract_user_role(self, request: Request) -> str:
        """Extract user role from request"""
        # Try to get from request state (set by auth middleware)
        if hasattr(request.state, 'current_user'):
            user = request.state.current_user
            if hasattr(user, 'role'):
                return user.role
        
        # Try to get from headers (for API keys)
        auth_header = request.headers.get('authorization', '')
        if 'Bearer' in auth_header:
            # This would need to be implemented based on your auth system
            return "authenticated"
        
        return "unknown"

class AdminPanelMetricsCollector:
    """Collects and updates admin panel metrics periodically"""
    
    def __init__(self):
        self.collection_interval = 30  # seconds
        self._running = False
        self._task = None
    
    async def start(self):
        """Start metrics collection"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Admin panel metrics collector started")
    
    async def stop(self):
        """Stop metrics collection"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Admin panel metrics collector stopped")
    
    async def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self._running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self):
        """Collect current metrics"""
        try:
            # This would integrate with your database and services
            # to collect current state metrics
            
            # Example: Update active users count
            # active_users = await self._get_active_users_by_role()
            # for role, count in active_users.items():
            #     admin_panel_metrics.update_active_users(role, "dashboard", count)
            
            # Example: Update moderation queue size
            # queue_sizes = await self._get_moderation_queue_sizes()
            # for priority, category, size in queue_sizes:
            #     admin_panel_metrics.update_moderation_queue(priority, category, size)
            
            # Example: Update notification queue sizes
            # notification_queues = await self._get_notification_queue_sizes()
            # for channel, priority, size in notification_queues:
            #     admin_panel_metrics.update_notification_queue(channel, priority, size)
            
            pass
            
        except Exception as e:
            logger.error(f"Error collecting admin panel metrics: {e}")
    
    async def _get_active_users_by_role(self) -> Dict[str, int]:
        """Get count of active users by role"""
        # This would query your database for active admin users
        # grouped by role in the last 5 minutes
        return {
            "super_admin": 1,
            "admin": 2,
            "moderator": 5,
            "analyst": 3,
            "marketing_manager": 2,
            "project_manager": 1
        }
    
    async def _get_moderation_queue_sizes(self) -> list:
        """Get moderation queue sizes by priority and category"""
        # This would query your moderation system
        return [
            ("high", "inappropriate_content", 5),
            ("medium", "quality_issues", 15),
            ("low", "minor_issues", 25)
        ]
    
    async def _get_notification_queue_sizes(self) -> list:
        """Get notification queue sizes by channel and priority"""
        # This would query your notification system
        return [
            ("email", "high", 10),
            ("email", "medium", 50),
            ("push", "high", 5),
            ("slack", "medium", 20)
        ]

# Global instance
admin_metrics_collector = AdminPanelMetricsCollector()

# Utility functions for manual metric recording
def record_user_action(user_role: str, action_type: str, module: str, success: bool = True):
    """Record a user action metric"""
    admin_panel_metrics.record_user_action(user_role, action_type, module, success)

def record_rbac_operation(changed_by_role: str, target_role: str, operation: str):
    """Record an RBAC operation metric"""
    admin_panel_metrics.record_rbac_operation(changed_by_role, target_role, operation)

def record_moderation_review(moderator_role: str, review_type: str, rating: int, response_time: float):
    """Record a moderation review metric"""
    admin_panel_metrics.record_moderation_review(moderator_role, review_type, rating, response_time)

def record_notification_sent(channel: str, notification_type: str, priority: str, 
                           status: str, delivery_time: float):
    """Record a notification metric"""
    admin_panel_metrics.record_notification_sent(
        channel, notification_type, priority, status, delivery_time
    )

def record_analytics_query(query_type: str, user_role: str, success: bool, 
                         duration: float, complexity: str = "medium"):
    """Record an analytics query metric"""
    admin_panel_metrics.record_analytics_query(
        query_type, user_role, success, duration, complexity
    )

def record_backup_operation(operation_type: str, backup_type: str, status: str, 
                          duration: float, size_bytes: int = 0):
    """Record a backup operation metric"""
    admin_panel_metrics.record_backup_operation(
        operation_type, backup_type, status, duration, size_bytes
    )

def record_feature_usage(feature: str, module: str, user_role: str, success: bool = True):
    """Record feature usage metric"""
    admin_panel_metrics.record_feature_usage(feature, module, user_role, success)