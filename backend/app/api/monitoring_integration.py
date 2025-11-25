"""
API endpoints for monitoring system integration with project management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_admin_user, get_current_user
from ..models.user import User
from ..models.monitoring_integration import IncidentStatus, IncidentSeverity, AlertStatus
from ..schemas.monitoring_integration import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentFilters,
    AlertCreate, AlertResponse, AlertFilters,
    OperationalDashboardResponse, PrometheusWebhook,
    TaskFromIncident, TaskFromAlert, IncidentStatistics, AlertStatistics
)
from ..services.monitoring_integration_service import monitoring_integration_service
from ..services.project_service import project_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Operational Dashboard
@router.get("/dashboard", response_model=OperationalDashboardResponse)
async def get_operational_dashboard(
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get operational metrics dashboard"""
    try:
        dashboard_data = await monitoring_integration_service.get_operational_dashboard(db, period)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting operational dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get operational dashboard")


# Incident Management
@router.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[List[IncidentStatus]] = Query(None),
    severity: Optional[List[IncidentSeverity]] = Query(None),
    assigned_to: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    source_system: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get list of incidents with optional filtering"""
    try:
        filters = IncidentFilters(
            status=status,
            severity=severity,
            assigned_to=assigned_to,
            project_id=project_id,
            source_system=source_system
        )
        
        incidents = await monitoring_integration_service.get_incidents(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters
        )
        return incidents
    except Exception as e:
        logger.error(f"Error getting incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get incidents")


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific incident"""
    try:
        incident = await monitoring_integration_service.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get incident")


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new incident"""
    try:
        incident = await monitoring_integration_service.create_incident(
            db, incident_data, current_user.id
        )
        return incident
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to create incident")


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing incident"""
    try:
        incident = await monitoring_integration_service.update_incident(
            db, incident_id, incident_data, current_user.id
        )
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update incident")


@router.post("/incidents/{incident_id}/create-task")
async def create_task_from_incident(
    incident_id: int,
    task_data: TaskFromIncident,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a task from an incident"""
    try:
        # Get the incident
        incident = await monitoring_integration_service.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Check if task already exists
        if incident.related_task_id:
            raise HTTPException(status_code=400, detail="Task already exists for this incident")
        
        # Create task using the monitoring integration service
        task = await monitoring_integration_service._create_incident_task(
            db, incident, task_data.project_id, current_user.id
        )
        
        if not task:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        # Update incident with task reference
        incident.related_task_id = task.id
        db.commit()
        
        return {
            "message": "Task created successfully",
            "task_id": task.id,
            "task_title": task.title,
            "incident_id": incident_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task from incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task from incident")


# Alert Management
@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[List[AlertStatus]] = Query(None),
    severity: Optional[List[IncidentSeverity]] = Query(None),
    source_system: Optional[List[str]] = Query(None),
    rule_name: Optional[List[str]] = Query(None),
    has_incident: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get list of alerts with optional filtering"""
    try:
        filters = AlertFilters(
            status=status,
            severity=severity,
            source_system=source_system,
            rule_name=rule_name,
            has_incident=has_incident
        )
        
        alerts = await monitoring_integration_service.get_alerts(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters
        )
        return alerts
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new alert (manual creation)"""
    try:
        alert = await monitoring_integration_service.create_alert(db, alert_data)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.post("/alerts/{alert_id}/create-task")
async def create_task_from_alert(
    alert_id: int,
    task_data: TaskFromAlert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a task from an alert"""
    try:
        # Get the alert
        alert = db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Check if task already exists
        if alert.created_task_id:
            raise HTTPException(status_code=400, detail="Task already exists for this alert")
        
        # Create task using the monitoring integration service
        task = await monitoring_integration_service._create_alert_task(db, alert)
        
        if not task:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        # Update alert with task reference
        alert.auto_task_created = True
        alert.created_task_id = task.id
        db.commit()
        
        return {
            "message": "Task created successfully",
            "task_id": task.id,
            "task_title": task.title,
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task from alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task from alert")


# Webhook endpoints for external monitoring systems
@router.post("/webhooks/prometheus")
async def prometheus_webhook(
    webhook_data: PrometheusWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook endpoint for Prometheus AlertManager"""
    try:
        logger.info(f"Received Prometheus webhook: {webhook_data.status}, {len(webhook_data.alerts)} alerts")
        
        # Process alerts in background
        background_tasks.add_task(
            process_prometheus_alerts,
            webhook_data,
            db
        )
        
        return {
            "status": "received",
            "alerts_count": len(webhook_data.alerts),
            "webhook_status": webhook_data.status
        }
        
    except Exception as e:
        logger.error(f"Error processing Prometheus webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/webhooks/grafana")
async def grafana_webhook(
    webhook_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook endpoint for Grafana alerts"""
    try:
        logger.info(f"Received Grafana webhook: {webhook_data}")
        
        # Process Grafana alert in background
        background_tasks.add_task(
            process_grafana_alert,
            webhook_data,
            db
        )
        
        return {
            "status": "received",
            "alert_id": webhook_data.get("id"),
            "alert_state": webhook_data.get("state")
        }
        
    except Exception as e:
        logger.error(f"Error processing Grafana webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


# Statistics endpoints
@router.get("/statistics/incidents", response_model=IncidentStatistics)
async def get_incident_statistics(
    period: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get incident statistics"""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_time = datetime.utcnow()
        if period == "24h":
            start_time = end_time - timedelta(hours=24)
        elif period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        else:
            start_time = end_time - timedelta(days=30)
        
        stats = await monitoring_integration_service._get_incident_statistics(db, start_time, end_time)
        
        # Add status breakdown
        status_counts = {}
        for status in IncidentStatus:
            count = db.query(Incident).filter(
                and_(
                    Incident.started_at >= start_time,
                    Incident.started_at <= end_time,
                    Incident.status == status
                )
            ).count()
            status_counts[status.value] = count
        
        stats["incidents_by_status"] = status_counts
        
        return IncidentStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Error getting incident statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get incident statistics")


@router.get("/statistics/alerts", response_model=AlertStatistics)
async def get_alert_statistics(
    period: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get alert statistics"""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_time = datetime.utcnow()
        if period == "24h":
            start_time = end_time - timedelta(hours=24)
        elif period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        else:
            start_time = end_time - timedelta(days=30)
        
        stats = await monitoring_integration_service._get_alert_statistics(db, start_time, end_time)
        
        # Add resolved alerts count
        resolved_alerts = db.query(MonitoringAlert).filter(
            and_(
                MonitoringAlert.resolved_at >= start_time,
                MonitoringAlert.resolved_at <= end_time
            )
        ).count()
        
        # Add alerts by rule breakdown
        rule_counts = {}
        rules_query = db.query(
            MonitoringAlert.rule_name,
            func.count(MonitoringAlert.id)
        ).filter(
            and_(
                MonitoringAlert.started_at >= start_time,
                MonitoringAlert.started_at <= end_time
            )
        ).group_by(MonitoringAlert.rule_name).all()
        
        for rule_name, count in rules_query:
            rule_counts[rule_name] = count
        
        stats["resolved_alerts"] = resolved_alerts
        stats["alerts_by_rule"] = rule_counts
        
        return AlertStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert statistics")


# Background task functions
async def process_prometheus_alerts(webhook_data: PrometheusWebhook, db: Session):
    """Process Prometheus alerts in background"""
    try:
        for alert in webhook_data.alerts:
            # Convert Prometheus alert to our alert format
            alert_data = AlertCreate(
                name=alert.labels.get("alertname", "Unknown Alert"),
                message=alert.annotations.get("summary", alert.annotations.get("description", "No description")),
                severity=_map_prometheus_severity(alert.labels.get("severity", "warning")),
                source_system="prometheus",
                rule_name=alert.labels.get("alertname", "unknown"),
                metric_name=alert.labels.get("__name__"),
                started_at=alert.startsAt,
                labels=alert.labels,
                annotations=alert.annotations
            )
            
            # Create alert
            await monitoring_integration_service.create_alert(db, alert_data)
            
        logger.info(f"Processed {len(webhook_data.alerts)} Prometheus alerts")
        
    except Exception as e:
        logger.error(f"Error processing Prometheus alerts: {e}")


async def process_grafana_alert(webhook_data: dict, db: Session):
    """Process Grafana alert in background"""
    try:
        # Convert Grafana alert to our alert format
        alert_data = AlertCreate(
            name=webhook_data.get("title", "Grafana Alert"),
            message=webhook_data.get("message", "No message"),
            severity=_map_grafana_severity(webhook_data.get("state", "alerting")),
            source_system="grafana",
            rule_name=webhook_data.get("ruleName", "unknown"),
            started_at=datetime.fromisoformat(webhook_data.get("time", datetime.utcnow().isoformat())),
            labels=webhook_data.get("tags", {}),
            annotations={
                "dashboard": webhook_data.get("dashboardId"),
                "panel": webhook_data.get("panelId"),
                "rule_url": webhook_data.get("ruleUrl")
            }
        )
        
        # Create alert
        await monitoring_integration_service.create_alert(db, alert_data)
        
        logger.info(f"Processed Grafana alert: {alert_data.name}")
        
    except Exception as e:
        logger.error(f"Error processing Grafana alert: {e}")


def _map_prometheus_severity(severity: str) -> IncidentSeverity:
    """Map Prometheus severity to our severity enum"""
    mapping = {
        "critical": IncidentSeverity.CRITICAL,
        "warning": IncidentSeverity.MEDIUM,
        "info": IncidentSeverity.LOW
    }
    return mapping.get(severity.lower(), IncidentSeverity.MEDIUM)


def _map_grafana_severity(state: str) -> IncidentSeverity:
    """Map Grafana state to our severity enum"""
    mapping = {
        "alerting": IncidentSeverity.HIGH,
        "pending": IncidentSeverity.MEDIUM,
        "ok": IncidentSeverity.LOW
    }
    return mapping.get(state.lower(), IncidentSeverity.MEDIUM)