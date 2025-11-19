"""
Enhanced Prometheus metrics for Admin Panel modules
Implements comprehensive monitoring for all admin panel features
"""

from prometheus_client import Counter, Histogram, Gauge, Info, Enum
from typing import Dict, Any, Optional
import time
from datetime import datetime
from enum import Enum as PyEnum

class AdminModuleType(PyEnum):
    """Admin panel module types"""
    DASHBOARD = "dashboard"
    USER_MANAGEMENT = "user_management"
    RBAC = "rbac"
    MODERATION = "moderation"
    MARKETING = "marketing"
    PROJECT = "project"
    NOTIFICATIONS = "notifications"
    ANALYTICS = "analytics"
    BACKUP = "backup"
    SYSTEM = "system"

class AdminPanelMetrics:
    """Comprehensive metrics for admin panel operations"""
    
    def __init__(self):
        # HTTP metrics for admin endpoints
        self.admin_http_requests = Counter(
            'admin_panel_http_requests_total',
            'Total HTTP requests to admin panel',
            ['module', 'endpoint', 'method', 'status_code', 'user_role']
        )
        
        self.admin_http_duration = Histogram(
            'admin_panel_http_request_duration_seconds',
            'HTTP request duration for admin panel',
            ['module', 'endpoint', 'method'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # User activity metrics
        self.admin_active_users = Gauge(
            'admin_panel_active_users',
            'Number of active admin users',
            ['role', 'module']
        )
        
        self.admin_user_sessions = Counter(
            'admin_panel_user_sessions_total',
            'Total admin user sessions',
            ['role', 'login_method']
        )
        
        self.admin_user_actions = Counter(
            'admin_panel_user_actions_total',
            'Total admin user actions',
            ['user_role', 'action_type', 'module', 'success']
        )
        
        # RBAC metrics
        self.rbac_role_changes = Counter(
            'admin_panel_rbac_role_changes_total',
            'Total role changes',
            ['changed_by_role', 'target_role', 'operation']
        )
        
        self.rbac_permission_checks = Counter(
            'admin_panel_rbac_permission_checks_total',
            'Total permission checks',
            ['user_role', 'resource', 'action', 'result']
        )
        
        self.rbac_active_roles = Gauge(
            'admin_panel_rbac_active_roles',
            'Number of active roles',
            ['role_type']
        )
        
        # Moderation metrics
        self.moderation_queue_size = Gauge(
            'admin_panel_moderation_queue_size',
            'Current moderation queue size',
            ['priority', 'category']
        )
        
        self.moderation_reviews = Counter(
            'admin_panel_moderation_reviews_total',
            'Total moderation reviews',
            ['moderator_role', 'review_type', 'rating']
        )
        
        self.moderation_response_time = Histogram(
            'admin_panel_moderation_response_time_seconds',
            'Time to complete moderation review',
            ['moderator_role', 'category'],
            buckets=[60, 300, 900, 1800, 3600, 7200]  # 1min to 2hours
        )
        
        # Marketing metrics
        self.marketing_campaigns = Gauge(
            'admin_panel_marketing_campaigns_active',
            'Number of active marketing campaigns',
            ['campaign_type', 'status']
        )
        
        self.marketing_conversions = Counter(
            'admin_panel_marketing_conversions_total',
            'Total marketing conversions',
            ['source', 'campaign', 'conversion_type']
        )
        
        self.marketing_funnel_stage = Gauge(
            'admin_panel_marketing_funnel_users',
            'Users in each funnel stage',
            ['stage', 'source']
        )
        
        # Project management metrics
        self.project_tasks = Gauge(
            'admin_panel_project_tasks',
            'Number of project tasks',
            ['status', 'priority', 'assigned_role']
        )
        
        self.project_milestones = Gauge(
            'admin_panel_project_milestones',
            'Number of project milestones',
            ['status', 'project']
        )
        
        self.project_resource_allocation = Gauge(
            'admin_panel_project_resource_allocation_percent',
            'Resource allocation percentage',
            ['user_role', 'project']
        )
        
        # Notification metrics
        self.notifications_sent = Counter(
            'admin_panel_notifications_sent_total',
            'Total notifications sent',
            ['channel', 'type', 'priority', 'status']
        )
        
        self.notifications_delivery_time = Histogram(
            'admin_panel_notifications_delivery_seconds',
            'Notification delivery time',
            ['channel', 'type'],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.notifications_queue_size = Gauge(
            'admin_panel_notifications_queue_size',
            'Current notification queue size',
            ['channel', 'priority']
        )
        
        # Analytics metrics
        self.analytics_queries = Counter(
            'admin_panel_analytics_queries_total',
            'Total analytics queries',
            ['query_type', 'user_role', 'success']
        )
        
        self.analytics_query_duration = Histogram(
            'admin_panel_analytics_query_duration_seconds',
            'Analytics query execution time',
            ['query_type', 'complexity'],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.analytics_dashboard_views = Counter(
            'admin_panel_analytics_dashboard_views_total',
            'Total dashboard views',
            ['dashboard_type', 'user_role']
        )
        
        # Backup system metrics
        self.backup_operations = Counter(
            'admin_panel_backup_operations_total',
            'Total backup operations',
            ['operation_type', 'backup_type', 'status']
        )
        
        self.backup_duration = Histogram(
            'admin_panel_backup_duration_seconds',
            'Backup operation duration',
            ['operation_type', 'backup_type'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400]  # 1min to 4hours
        )
        
        self.backup_size = Gauge(
            'admin_panel_backup_size_bytes',
            'Backup size in bytes',
            ['backup_type', 'retention_period']
        )
        
        # System performance metrics
        self.admin_panel_errors = Counter(
            'admin_panel_errors_total',
            'Total admin panel errors',
            ['module', 'error_type', 'severity']
        )
        
        self.admin_panel_cache_hits = Counter(
            'admin_panel_cache_hits_total',
            'Total cache hits',
            ['cache_type', 'module']
        )
        
        self.admin_panel_cache_misses = Counter(
            'admin_panel_cache_misses_total',
            'Total cache misses',
            ['cache_type', 'module']
        )
        
        # Real-time metrics
        self.websocket_connections = Gauge(
            'admin_panel_websocket_connections',
            'Active WebSocket connections',
            ['connection_type', 'user_role']
        )
        
        self.realtime_updates = Counter(
            'admin_panel_realtime_updates_total',
            'Total real-time updates sent',
            ['update_type', 'module', 'recipient_role']
        )
        
        # Feature usage metrics
        self.feature_usage = Counter(
            'admin_panel_feature_usage_total',
            'Feature usage counter',
            ['feature', 'module', 'user_role', 'success']
        )
        
        self.feature_adoption = Gauge(
            'admin_panel_feature_adoption_rate',
            'Feature adoption rate (0-1)',
            ['feature', 'module', 'time_period']
        )
        
        # Performance optimization metrics
        self.code_splitting_loads = Counter(
            'admin_panel_code_splitting_loads_total',
            'Code splitting chunk loads',
            ['chunk_name', 'load_time_bucket']
        )
        
        self.lazy_loading_triggers = Counter(
            'admin_panel_lazy_loading_triggers_total',
            'Lazy loading triggers',
            ['component_type', 'trigger_reason']
        )
        
        # Info metrics
        self.admin_panel_info = Info(
            'admin_panel_info',
            'Admin panel information'
        )
        
        # Set initial info
        self.admin_panel_info.info({
            'version': '2.0.0',
            'build_date': datetime.now().isoformat(),
            'modules': ','.join([m.value for m in AdminModuleType])
        })
    
    def record_http_request(self, module: str, endpoint: str, method: str, 
                          status_code: int, duration: float, user_role: str = "unknown"):
        """Record HTTP request metrics"""
        self.admin_http_requests.labels(
            module=module,
            endpoint=endpoint,
            method=method,
            status_code=str(status_code),
            user_role=user_role
        ).inc()
        
        self.admin_http_duration.labels(
            module=module,
            endpoint=endpoint,
            method=method
        ).observe(duration)
    
    def record_user_action(self, user_role: str, action_type: str, 
                          module: str, success: bool = True):
        """Record user action metrics"""
        self.admin_user_actions.labels(
            user_role=user_role,
            action_type=action_type,
            module=module,
            success=str(success).lower()
        ).inc()
    
    def update_active_users(self, role: str, module: str, count: int):
        """Update active users gauge"""
        self.admin_active_users.labels(role=role, module=module).set(count)
    
    def record_rbac_operation(self, changed_by_role: str, target_role: str, 
                            operation: str):
        """Record RBAC operation"""
        self.rbac_role_changes.labels(
            changed_by_role=changed_by_role,
            target_role=target_role,
            operation=operation
        ).inc()
    
    def record_permission_check(self, user_role: str, resource: str, 
                              action: str, result: bool):
        """Record permission check"""
        self.rbac_permission_checks.labels(
            user_role=user_role,
            resource=resource,
            action=action,
            result=str(result).lower()
        ).inc()
    
    def update_moderation_queue(self, priority: str, category: str, size: int):
        """Update moderation queue size"""
        self.moderation_queue_size.labels(
            priority=priority,
            category=category
        ).set(size)
    
    def record_moderation_review(self, moderator_role: str, review_type: str, 
                               rating: int, response_time: float):
        """Record moderation review"""
        self.moderation_reviews.labels(
            moderator_role=moderator_role,
            review_type=review_type,
            rating=str(rating)
        ).inc()
        
        self.moderation_response_time.labels(
            moderator_role=moderator_role,
            category=review_type
        ).observe(response_time)
    
    def update_marketing_campaigns(self, campaign_type: str, status: str, count: int):
        """Update marketing campaigns gauge"""
        self.marketing_campaigns.labels(
            campaign_type=campaign_type,
            status=status
        ).set(count)
    
    def record_marketing_conversion(self, source: str, campaign: str, 
                                  conversion_type: str):
        """Record marketing conversion"""
        self.marketing_conversions.labels(
            source=source,
            campaign=campaign,
            conversion_type=conversion_type
        ).inc()
    
    def update_project_tasks(self, status: str, priority: str, 
                           assigned_role: str, count: int):
        """Update project tasks gauge"""
        self.project_tasks.labels(
            status=status,
            priority=priority,
            assigned_role=assigned_role
        ).set(count)
    
    def record_notification_sent(self, channel: str, notification_type: str, 
                               priority: str, status: str, delivery_time: float):
        """Record notification metrics"""
        self.notifications_sent.labels(
            channel=channel,
            type=notification_type,
            priority=priority,
            status=status
        ).inc()
        
        self.notifications_delivery_time.labels(
            channel=channel,
            type=notification_type
        ).observe(delivery_time)
    
    def update_notification_queue(self, channel: str, priority: str, size: int):
        """Update notification queue size"""
        self.notifications_queue_size.labels(
            channel=channel,
            priority=priority
        ).set(size)
    
    def record_analytics_query(self, query_type: str, user_role: str, 
                             success: bool, duration: float, complexity: str = "medium"):
        """Record analytics query metrics"""
        self.analytics_queries.labels(
            query_type=query_type,
            user_role=user_role,
            success=str(success).lower()
        ).inc()
        
        self.analytics_query_duration.labels(
            query_type=query_type,
            complexity=complexity
        ).observe(duration)
    
    def record_dashboard_view(self, dashboard_type: str, user_role: str):
        """Record dashboard view"""
        self.analytics_dashboard_views.labels(
            dashboard_type=dashboard_type,
            user_role=user_role
        ).inc()
    
    def record_backup_operation(self, operation_type: str, backup_type: str, 
                              status: str, duration: float, size_bytes: int = 0):
        """Record backup operation metrics"""
        self.backup_operations.labels(
            operation_type=operation_type,
            backup_type=backup_type,
            status=status
        ).inc()
        
        self.backup_duration.labels(
            operation_type=operation_type,
            backup_type=backup_type
        ).observe(duration)
        
        if size_bytes > 0:
            self.backup_size.labels(
                backup_type=backup_type,
                retention_period="30d"  # Default retention
            ).set(size_bytes)
    
    def record_error(self, module: str, error_type: str, severity: str = "error"):
        """Record admin panel error"""
        self.admin_panel_errors.labels(
            module=module,
            error_type=error_type,
            severity=severity
        ).inc()
    
    def record_cache_operation(self, cache_type: str, module: str, hit: bool):
        """Record cache operation"""
        if hit:
            self.admin_panel_cache_hits.labels(
                cache_type=cache_type,
                module=module
            ).inc()
        else:
            self.admin_panel_cache_misses.labels(
                cache_type=cache_type,
                module=module
            ).inc()
    
    def update_websocket_connections(self, connection_type: str, 
                                   user_role: str, count: int):
        """Update WebSocket connections gauge"""
        self.websocket_connections.labels(
            connection_type=connection_type,
            user_role=user_role
        ).set(count)
    
    def record_realtime_update(self, update_type: str, module: str, 
                             recipient_role: str):
        """Record real-time update"""
        self.realtime_updates.labels(
            update_type=update_type,
            module=module,
            recipient_role=recipient_role
        ).inc()
    
    def record_feature_usage(self, feature: str, module: str, 
                           user_role: str, success: bool = True):
        """Record feature usage"""
        self.feature_usage.labels(
            feature=feature,
            module=module,
            user_role=user_role,
            success=str(success).lower()
        ).inc()
    
    def update_feature_adoption(self, feature: str, module: str, 
                              time_period: str, rate: float):
        """Update feature adoption rate"""
        self.feature_adoption.labels(
            feature=feature,
            module=module,
            time_period=time_period
        ).set(rate)
    
    def record_code_splitting_load(self, chunk_name: str, load_time: float):
        """Record code splitting chunk load"""
        # Categorize load time
        if load_time < 0.5:
            bucket = "fast"
        elif load_time < 2.0:
            bucket = "medium"
        else:
            bucket = "slow"
            
        self.code_splitting_loads.labels(
            chunk_name=chunk_name,
            load_time_bucket=bucket
        ).inc()
    
    def record_lazy_loading_trigger(self, component_type: str, trigger_reason: str):
        """Record lazy loading trigger"""
        self.lazy_loading_triggers.labels(
            component_type=component_type,
            trigger_reason=trigger_reason
        ).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        return {
            "timestamp": time.time(),
            "admin_panel_version": "2.0.0",
            "metrics_collected": True,
            "modules_monitored": [m.value for m in AdminModuleType]
        }

# Global instance
admin_panel_metrics = AdminPanelMetrics()