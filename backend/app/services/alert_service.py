"""
Alert Service for Admin Panel
Comprehensive alerting system with integration to notification service
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.core.admin_panel_metrics import admin_panel_metrics
from app.core.jaeger_tracing import jaeger_tracing, trace_function
from app.services.notification_service import notification_service
from app.utils.performance_audit import performance_auditor

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    duration: int  # seconds
    enabled: bool = True
    tags: Dict[str, str] = None
    notification_channels: List[str] = None
    suppression_rules: List[Dict] = None
    escalation_rules: List[Dict] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.notification_channels is None:
            self.notification_channels = ["email"]
        if self.suppression_rules is None:
            self.suppression_rules = []
        if self.escalation_rules is None:
            self.escalation_rules = []

@dataclass
class Alert:
    """Active alert instance"""
    id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    metric_name: str
    current_value: float
    threshold: float
    started_at: datetime
    last_updated: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    tags: Dict[str, str] = None
    annotations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.annotations is None:
            self.annotations = {}

class AlertManager:
    """Comprehensive alert management system"""
    
    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppression_groups: Dict[str, List[str]] = {}
        self.escalation_timers: Dict[str, asyncio.Task] = {}
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules for admin panel"""
        default_rules = [
            # System performance alerts
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above threshold",
                metric_name="cpu_usage",
                condition="gt",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration=300,  # 5 minutes
                notification_channels=["email", "slack"],
                tags={"category": "system", "component": "cpu"}
            ),
            
            AlertRule(
                id="critical_cpu_usage",
                name="Critical CPU Usage",
                description="CPU usage is critically high",
                metric_name="cpu_usage",
                condition="gt",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,  # 1 minute
                notification_channels=["email", "slack", "sms"],
                tags={"category": "system", "component": "cpu"}
            ),
            
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is above threshold",
                metric_name="memory_usage",
                condition="gt",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                notification_channels=["email", "slack"],
                tags={"category": "system", "component": "memory"}
            ),
            
            # Admin panel specific alerts
            AlertRule(
                id="admin_panel_high_error_rate",
                name="Admin Panel High Error Rate",
                description="Admin panel error rate is above threshold",
                metric_name="admin_panel_error_rate",
                condition="gt",
                threshold=5.0,
                severity=AlertSeverity.CRITICAL,
                duration=120,
                notification_channels=["email", "slack"],
                tags={"category": "admin_panel", "component": "api"}
            ),
            
            AlertRule(
                id="slow_admin_response_time",
                name="Slow Admin Panel Response Time",
                description="Admin panel response time is too slow",
                metric_name="admin_response_time_p95",
                condition="gt",
                threshold=5.0,
                severity=AlertSeverity.WARNING,
                duration=180,
                notification_channels=["email"],
                tags={"category": "admin_panel", "component": "performance"}
            ),
            
            AlertRule(
                id="moderation_queue_backlog",
                name="Moderation Queue Backlog",
                description="Moderation queue has too many pending items",
                metric_name="moderation_queue_size",
                condition="gt",
                threshold=100.0,
                severity=AlertSeverity.WARNING,
                duration=600,  # 10 minutes
                notification_channels=["email", "slack"],
                tags={"category": "admin_panel", "component": "moderation"}
            ),
            
            AlertRule(
                id="notification_delivery_failure",
                name="High Notification Delivery Failure Rate",
                description="Notification delivery failure rate is high",
                metric_name="notification_failure_rate",
                condition="gt",
                threshold=10.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                notification_channels=["email", "slack"],
                tags={"category": "admin_panel", "component": "notifications"}
            ),
            
            # Database alerts
            AlertRule(
                id="database_connection_limit",
                name="Database Connection Limit Reached",
                description="Database connection count is near limit",
                metric_name="database_connections",
                condition="gt",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                notification_channels=["email", "slack", "sms"],
                tags={"category": "database", "component": "connections"}
            ),
            
            AlertRule(
                id="slow_database_queries",
                name="Slow Database Queries",
                description="Database query response time is too slow",
                metric_name="database_query_time_p95",
                condition="gt",
                threshold=3.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                notification_channels=["email"],
                tags={"category": "database", "component": "performance"}
            ),
            
            # Cache alerts
            AlertRule(
                id="low_cache_hit_rate",
                name="Low Cache Hit Rate",
                description="Cache hit rate is below optimal threshold",
                metric_name="cache_hit_rate",
                condition="lt",
                threshold=70.0,
                severity=AlertSeverity.WARNING,
                duration=600,
                notification_channels=["email"],
                tags={"category": "cache", "component": "performance"}
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
    
    @trace_function("alert_evaluation")
    async def evaluate_alerts(self, metrics: Dict[str, float]):
        """Evaluate all alert rules against current metrics"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            metric_value = metrics.get(rule.metric_name)
            if metric_value is None:
                continue
            
            # Check if condition is met
            condition_met = self._evaluate_condition(
                metric_value, rule.condition, rule.threshold
            )
            
            existing_alert = self.active_alerts.get(rule_id)
            
            if condition_met:
                if existing_alert:
                    # Update existing alert
                    existing_alert.current_value = metric_value
                    existing_alert.last_updated = datetime.utcnow()
                else:
                    # Create new alert
                    alert = Alert(
                        id=f"{rule_id}_{int(datetime.utcnow().timestamp())}",
                        rule_id=rule_id,
                        name=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        status=AlertStatus.ACTIVE,
                        metric_name=rule.metric_name,
                        current_value=metric_value,
                        threshold=rule.threshold,
                        started_at=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        tags=rule.tags.copy()
                    )
                    
                    self.active_alerts[rule_id] = alert
                    await self._trigger_alert(alert, rule)
            else:
                if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                    # Resolve alert
                    await self._resolve_alert(existing_alert, rule)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        conditions = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
            "ne": lambda v, t: v != t
        }
        
        return conditions.get(condition, lambda v, t: False)(value, threshold)
    
    @trace_function("alert_trigger")
    async def _trigger_alert(self, alert: Alert, rule: AlertRule):
        """Trigger alert and send notifications"""
        logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
        
        # Record alert metric
        admin_panel_metrics.record_error(
            module="alert_system",
            error_type="alert_triggered",
            severity=alert.severity.value
        )
        
        # Check suppression rules
        if self._is_suppressed(alert, rule):
            alert.status = AlertStatus.SUPPRESSED
            logger.info(f"Alert suppressed: {alert.name}")
            return
        
        # Send notifications
        await self._send_alert_notifications(alert, rule)
        
        # Set up escalation if configured
        if rule.escalation_rules:
            await self._setup_escalation(alert, rule)
    
    @trace_function("alert_resolve")
    async def _resolve_alert(self, alert: Alert, rule: AlertRule):
        """Resolve an active alert"""
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.last_updated = datetime.utcnow()
        
        logger.info(f"Alert resolved: {alert.name}")
        
        # Send resolution notification
        await self._send_resolution_notification(alert, rule)
        
        # Move to history and remove from active alerts
        self.alert_history.append(alert)
        if alert.rule_id in self.active_alerts:
            del self.active_alerts[alert.rule_id]
        
        # Cancel escalation timer if exists
        if alert.id in self.escalation_timers:
            self.escalation_timers[alert.id].cancel()
            del self.escalation_timers[alert.id]
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert notifications through configured channels"""
        notification_data = {
            "alert_id": alert.id,
            "alert_name": alert.name,
            "description": alert.description,
            "severity": alert.severity.value,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "started_at": alert.started_at.isoformat(),
            "tags": alert.tags
        }
        
        for channel in rule.notification_channels:
            try:
                await notification_service.send_notification(
                    channel=channel,
                    notification_type="alert",
                    title=f"🚨 {alert.name}",
                    message=self._format_alert_message(alert),
                    priority="high" if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY] else "medium",
                    data=notification_data
                )
            except Exception as e:
                logger.error(f"Failed to send alert notification via {channel}: {e}")
    
    async def _send_resolution_notification(self, alert: Alert, rule: AlertRule):
        """Send alert resolution notification"""
        notification_data = {
            "alert_id": alert.id,
            "alert_name": alert.name,
            "resolved_at": alert.resolved_at.isoformat(),
            "duration": str(alert.resolved_at - alert.started_at)
        }
        
        for channel in rule.notification_channels:
            try:
                await notification_service.send_notification(
                    channel=channel,
                    notification_type="alert_resolution",
                    title=f"✅ Resolved: {alert.name}",
                    message=f"Alert '{alert.name}' has been resolved.",
                    priority="low",
                    data=notification_data
                )
            except Exception as e:
                logger.error(f"Failed to send resolution notification via {channel}: {e}")
    
    def _format_alert_message(self, alert: Alert) -> str:
        """Format alert message for notifications"""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.EMERGENCY: "🆘"
        }
        
        emoji = severity_emoji.get(alert.severity, "🔔")
        
        message = f"{emoji} {alert.name}\n\n"
        message += f"Description: {alert.description}\n"
        message += f"Metric: {alert.metric_name}\n"
        message += f"Current Value: {alert.current_value}\n"
        message += f"Threshold: {alert.threshold}\n"
        message += f"Started: {alert.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if alert.tags:
            message += f"Tags: {', '.join([f'{k}={v}' for k, v in alert.tags.items()])}\n"
        
        return message
    
    def _is_suppressed(self, alert: Alert, rule: AlertRule) -> bool:
        """Check if alert should be suppressed"""
        for suppression_rule in rule.suppression_rules:
            # Implement suppression logic based on time, tags, etc.
            if self._matches_suppression_rule(alert, suppression_rule):
                return True
        return False
    
    def _matches_suppression_rule(self, alert: Alert, suppression_rule: Dict) -> bool:
        """Check if alert matches suppression rule"""
        # Example suppression rule matching
        if "time_range" in suppression_rule:
            current_time = datetime.utcnow().time()
            start_time = datetime.strptime(suppression_rule["time_range"]["start"], "%H:%M").time()
            end_time = datetime.strptime(suppression_rule["time_range"]["end"], "%H:%M").time()
            
            if start_time <= current_time <= end_time:
                return True
        
        if "tags" in suppression_rule:
            for key, value in suppression_rule["tags"].items():
                if alert.tags.get(key) == value:
                    return True
        
        return False
    
    async def _setup_escalation(self, alert: Alert, rule: AlertRule):
        """Set up alert escalation"""
        for escalation_rule in rule.escalation_rules:
            delay = escalation_rule.get("delay", 3600)  # Default 1 hour
            
            async def escalate():
                await asyncio.sleep(delay)
                if alert.id in self.active_alerts and alert.status == AlertStatus.ACTIVE:
                    await self._escalate_alert(alert, escalation_rule)
            
            task = asyncio.create_task(escalate())
            self.escalation_timers[alert.id] = task
    
    async def _escalate_alert(self, alert: Alert, escalation_rule: Dict):
        """Escalate alert to higher severity or different channels"""
        logger.warning(f"Escalating alert: {alert.name}")
        
        # Increase severity if specified
        if "severity" in escalation_rule:
            new_severity = AlertSeverity(escalation_rule["severity"])
            if new_severity != alert.severity:
                alert.severity = new_severity
                alert.last_updated = datetime.utcnow()
        
        # Send to additional channels
        additional_channels = escalation_rule.get("channels", [])
        for channel in additional_channels:
            try:
                await notification_service.send_notification(
                    channel=channel,
                    notification_type="alert_escalation",
                    title=f"🔥 ESCALATED: {alert.name}",
                    message=f"Alert has been escalated due to no resolution.\n\n{self._format_alert_message(alert)}",
                    priority="high",
                    data={"alert_id": alert.id, "escalated": True}
                )
            except Exception as e:
                logger.error(f"Failed to send escalation notification via {channel}: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        for rule_id, alert in self.active_alerts.items():
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                alert.last_updated = datetime.utcnow()
                
                logger.info(f"Alert acknowledged by {acknowledged_by}: {alert.name}")
                return True
        
        return False
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule"""
        try:
            self.alert_rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add alert rule: {e}")
            return False
    
    def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule"""
        if rule_id not in self.alert_rules:
            return False
        
        try:
            rule = self.alert_rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            logger.info(f"Updated alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update alert rule: {e}")
            return False
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        if rule_id not in self.alert_rules:
            return False
        
        try:
            rule = self.alert_rules.pop(rule_id)
            
            # Resolve any active alerts for this rule
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                self.alert_history.append(alert)
                del self.active_alerts[rule_id]
            
            logger.info(f"Deleted alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete alert rule: {e}")
            return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [asdict(alert) for alert in self.active_alerts.values()]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        return [asdict(alert) for alert in self.alert_history[-limit:]]
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules"""
        return [asdict(rule) for rule in self.alert_rules.values()]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_rules = len(self.alert_rules)
        enabled_rules = sum(1 for rule in self.alert_rules.values() if rule.enabled)
        active_alerts = len(self.active_alerts)
        
        severity_counts = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "active_alerts": active_alerts,
            "alerts_by_severity": severity_counts,
            "total_history": len(self.alert_history),
            "timestamp": datetime.utcnow().isoformat()
        }

# Background task for continuous alert evaluation
class AlertEvaluationService:
    """Service for continuous alert evaluation"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.evaluation_interval = 30  # seconds
        self._running = False
        self._task = None
    
    async def start(self):
        """Start alert evaluation service"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._evaluation_loop())
        logger.info("Alert evaluation service started")
    
    async def stop(self):
        """Stop alert evaluation service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Alert evaluation service stopped")
    
    async def _evaluation_loop(self):
        """Main alert evaluation loop"""
        while self._running:
            try:
                # Get current metrics (this would integrate with your metrics system)
                metrics = await self._collect_current_metrics()
                
                # Evaluate alerts
                await self.alert_manager.evaluate_alerts(metrics)
                
                await asyncio.sleep(self.evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(self.evaluation_interval)
    
    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current metrics for alert evaluation"""
        try:
            # This would integrate with your actual metrics collection
            # For now, we'll get some basic system metrics
            import psutil
            
            metrics = {
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
            }
            
            # Add simulated admin panel metrics
            metrics.update({
                "admin_panel_error_rate": 0.5,  # Would come from actual metrics
                "admin_response_time_p95": 1.2,
                "moderation_queue_size": 25,
                "notification_failure_rate": 2.0,
                "database_connections": 45,
                "database_query_time_p95": 0.8,
                "cache_hit_rate": 85.0
            })
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}

# Global instances
alert_manager = AlertManager()
alert_evaluation_service = AlertEvaluationService(alert_manager)