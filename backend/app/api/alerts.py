"""
Alert Management API Endpoints
RESTful API for managing alerts and alert rules
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.permissions import get_current_admin_user
from app.models.user import User
from app.services.alert_service import alert_manager, AlertRule, AlertSeverity
from app.core.admin_panel_metrics import admin_panel_metrics
from app.middleware.admin_panel_monitoring import record_user_action

router = APIRouter()

# Pydantic models for API
class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    metric_name: str = Field(..., min_length=1, max_length=50)
    condition: str = Field(..., pattern="^(gt|gte|lt|lte|eq|ne)$")
    threshold: float
    severity: str = Field(..., pattern="^(info|warning|critical|emergency)$")
    duration: int = Field(..., ge=1, le=86400)  # 1 second to 24 hours
    enabled: bool = True
    tags: Optional[Dict[str, str]] = {}
    notification_channels: Optional[List[str]] = ["email"]
    suppression_rules: Optional[List[Dict]] = []
    escalation_rules: Optional[List[Dict]] = []

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    condition: Optional[str] = Field(None, pattern="^(gt|gte|lt|lte|eq|ne)$")
    threshold: Optional[float] = None
    severity: Optional[str] = Field(None, pattern="^(info|warning|critical|emergency)$")
    duration: Optional[int] = Field(None, ge=1, le=86400)
    enabled: Optional[bool] = None
    tags: Optional[Dict[str, str]] = None
    notification_channels: Optional[List[str]] = None
    suppression_rules: Optional[List[Dict]] = None
    escalation_rules: Optional[List[Dict]] = None

class AlertAcknowledge(BaseModel):
    alert_id: str
    comment: Optional[str] = None

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_alert_rules(
    current_user: User = Depends(get_current_admin_user),
    enabled_only: bool = Query(False, description="Return only enabled rules")
):
    """Get all alert rules"""
    try:
        record_user_action(current_user.role, "view_alert_rules", "alerts", True)
        
        rules = alert_manager.get_alert_rules()
        
        if enabled_only:
            rules = [rule for rule in rules if rule.get("enabled", True)]
        
        return {
            "success": True,
            "data": rules,
            "total": len(rules),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        record_user_action(current_user.role, "view_alert_rules", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to get alert rules: {str(e)}")

@router.post("/rules", response_model=Dict[str, Any])
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new alert rule"""
    try:
        # Check permissions (only super_admin and admin can create rules)
        if current_user.role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to create alert rules")
        
        # Generate unique ID
        rule_id = f"custom_{rule_data.name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"
        
        # Create alert rule
        alert_rule = AlertRule(
            id=rule_id,
            name=rule_data.name,
            description=rule_data.description,
            metric_name=rule_data.metric_name,
            condition=rule_data.condition,
            threshold=rule_data.threshold,
            severity=AlertSeverity(rule_data.severity),
            duration=rule_data.duration,
            enabled=rule_data.enabled,
            tags=rule_data.tags or {},
            notification_channels=rule_data.notification_channels or ["email"],
            suppression_rules=rule_data.suppression_rules or [],
            escalation_rules=rule_data.escalation_rules or []
        )
        
        success = alert_manager.add_alert_rule(alert_rule)
        
        if success:
            record_user_action(current_user.role, "create_alert_rule", "alerts", True)
            admin_panel_metrics.record_user_action(current_user.role, "create_alert_rule", "alerts", True)
            
            return {
                "success": True,
                "message": "Alert rule created successfully",
                "rule_id": rule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create alert rule")
            
    except HTTPException:
        raise
    except Exception as e:
        record_user_action(current_user.role, "create_alert_rule", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")

@router.put("/rules/{rule_id}", response_model=Dict[str, Any])
async def update_alert_rule(
    rule_id: str,
    rule_updates: AlertRuleUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing alert rule"""
    try:
        # Check permissions
        if current_user.role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to update alert rules")
        
        # Convert to dict and remove None values
        updates = {k: v for k, v in rule_updates.dict().items() if v is not None}
        
        # Convert severity string to enum if provided
        if "severity" in updates:
            updates["severity"] = AlertSeverity(updates["severity"])
        
        success = alert_manager.update_alert_rule(rule_id, updates)
        
        if success:
            record_user_action(current_user.role, "update_alert_rule", "alerts", True)
            admin_panel_metrics.record_user_action(current_user.role, "update_alert_rule", "alerts", True)
            
            return {
                "success": True,
                "message": "Alert rule updated successfully",
                "rule_id": rule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert rule not found")
            
    except HTTPException:
        raise
    except Exception as e:
        record_user_action(current_user.role, "update_alert_rule", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")

@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete an alert rule"""
    try:
        # Check permissions
        if current_user.role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to delete alert rules")
        
        success = alert_manager.delete_alert_rule(rule_id)
        
        if success:
            record_user_action(current_user.role, "delete_alert_rule", "alerts", True)
            admin_panel_metrics.record_user_action(current_user.role, "delete_alert_rule", "alerts", True)
            
            return {
                "success": True,
                "message": "Alert rule deleted successfully",
                "rule_id": rule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert rule not found")
            
    except HTTPException:
        raise
    except Exception as e:
        record_user_action(current_user.role, "delete_alert_rule", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")

@router.get("/active", response_model=Dict[str, Any])
async def get_active_alerts(
    current_user: User = Depends(get_current_admin_user),
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical|emergency)$"),
    limit: int = Query(50, ge=1, le=500)
):
    """Get active alerts"""
    try:
        record_user_action(current_user.role, "view_active_alerts", "alerts", True)
        
        alerts = alert_manager.get_active_alerts()
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        # Limit results
        alerts = alerts[:limit]
        
        return {
            "success": True,
            "data": alerts,
            "total": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        record_user_action(current_user.role, "view_active_alerts", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to get active alerts: {str(e)}")

@router.get("/history", response_model=Dict[str, Any])
async def get_alert_history(
    current_user: User = Depends(get_current_admin_user),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical|emergency)$")
):
    """Get alert history"""
    try:
        record_user_action(current_user.role, "view_alert_history", "alerts", True)
        
        history = alert_manager.get_alert_history(limit)
        
        # Filter by severity if specified
        if severity:
            history = [alert for alert in history if alert.get("severity") == severity]
        
        return {
            "success": True,
            "data": history,
            "total": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        record_user_action(current_user.role, "view_alert_history", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")

@router.post("/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(
    acknowledge_data: AlertAcknowledge,
    current_user: User = Depends(get_current_admin_user)
):
    """Acknowledge an active alert"""
    try:
        success = await alert_manager.acknowledge_alert(
            acknowledge_data.alert_id,
            current_user.username or current_user.email
        )
        
        if success:
            record_user_action(current_user.role, "acknowledge_alert", "alerts", True)
            admin_panel_metrics.record_user_action(current_user.role, "acknowledge_alert", "alerts", True)
            
            return {
                "success": True,
                "message": "Alert acknowledged successfully",
                "alert_id": acknowledge_data.alert_id,
                "acknowledged_by": current_user.username or current_user.email,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
    except HTTPException:
        raise
    except Exception as e:
        record_user_action(current_user.role, "acknowledge_alert", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/statistics", response_model=Dict[str, Any])
async def get_alert_statistics(
    current_user: User = Depends(get_current_admin_user)
):
    """Get alert system statistics"""
    try:
        record_user_action(current_user.role, "view_alert_statistics", "alerts", True)
        
        stats = alert_manager.get_alert_statistics()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        record_user_action(current_user.role, "view_alert_statistics", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to get alert statistics: {str(e)}")

@router.post("/test-rule/{rule_id}", response_model=Dict[str, Any])
async def test_alert_rule(
    rule_id: str,
    test_value: float = Body(..., embed=True),
    current_user: User = Depends(get_current_admin_user)
):
    """Test an alert rule with a specific value"""
    try:
        # Check permissions
        if current_user.role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to test alert rules")
        
        rules = alert_manager.get_alert_rules()
        rule = next((r for r in rules if r["id"] == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        # Simulate alert evaluation
        condition_met = alert_manager._evaluate_condition(
            test_value, rule["condition"], rule["threshold"]
        )
        
        record_user_action(current_user.role, "test_alert_rule", "alerts", True)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "test_value": test_value,
            "threshold": rule["threshold"],
            "condition": rule["condition"],
            "condition_met": condition_met,
            "would_trigger": condition_met,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        record_user_action(current_user.role, "test_alert_rule", "alerts", False)
        raise HTTPException(status_code=500, detail=f"Failed to test alert rule: {str(e)}")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_available_metrics(
    current_user: User = Depends(get_current_admin_user)
):
    """Get list of available metrics for alert rules"""
    try:
        # Define available metrics that can be used in alert rules
        available_metrics = [
            {
                "name": "cpu_usage",
                "description": "System CPU usage percentage",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "memory_usage",
                "description": "System memory usage percentage",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "disk_usage",
                "description": "System disk usage percentage",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "admin_panel_error_rate",
                "description": "Admin panel error rate percentage",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "admin_response_time_p95",
                "description": "Admin panel 95th percentile response time",
                "unit": "seconds",
                "type": "histogram"
            },
            {
                "name": "moderation_queue_size",
                "description": "Number of items in moderation queue",
                "unit": "items",
                "type": "gauge"
            },
            {
                "name": "notification_failure_rate",
                "description": "Notification delivery failure rate",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "database_connections",
                "description": "Number of active database connections",
                "unit": "connections",
                "type": "gauge"
            },
            {
                "name": "database_query_time_p95",
                "description": "Database query 95th percentile response time",
                "unit": "seconds",
                "type": "histogram"
            },
            {
                "name": "cache_hit_rate",
                "description": "Cache hit rate percentage",
                "unit": "%",
                "type": "gauge"
            }
        ]
        
        return {
            "success": True,
            "data": available_metrics,
            "total": len(available_metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available metrics: {str(e)}")

@router.get("/channels", response_model=Dict[str, Any])
async def get_notification_channels(
    current_user: User = Depends(get_current_admin_user)
):
    """Get available notification channels"""
    try:
        channels = [
            {
                "name": "email",
                "description": "Email notifications",
                "enabled": True,
                "config_required": ["smtp_server", "smtp_port", "username", "password"]
            },
            {
                "name": "slack",
                "description": "Slack notifications",
                "enabled": True,
                "config_required": ["webhook_url", "channel"]
            },
            {
                "name": "telegram",
                "description": "Telegram notifications",
                "enabled": True,
                "config_required": ["bot_token", "chat_id"]
            },
            {
                "name": "sms",
                "description": "SMS notifications",
                "enabled": False,
                "config_required": ["provider", "api_key", "phone_numbers"]
            },
            {
                "name": "webhook",
                "description": "Custom webhook notifications",
                "enabled": True,
                "config_required": ["url", "method", "headers"]
            }
        ]
        
        return {
            "success": True,
            "data": channels,
            "total": len(channels),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification channels: {str(e)}")