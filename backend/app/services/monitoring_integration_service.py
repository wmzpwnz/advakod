"""
Service for integrating monitoring system with project management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError

from ..models.monitoring_integration import (
    Incident, MonitoringAlert, IncidentUpdate, OperationalMetric, MetricValue,
    IncidentStatus, IncidentSeverity, AlertStatus
)
from ..models.project import Task, Project, TaskStatus, TaskType, TaskPriority
from ..models.user import User
from ..schemas.monitoring_integration import (
    IncidentCreate, IncidentUpdate as IncidentUpdateSchema, IncidentResponse,
    AlertCreate, AlertResponse, OperationalDashboardResponse,
    MetricResponse, IncidentFilters, AlertFilters
)
from .project_service import project_service
from .unified_monitoring_service import unified_monitoring_service

logger = logging.getLogger(__name__)


class MonitoringIntegrationService:
    """Service for monitoring system integration with project management"""

    def __init__(self):
        self.logger = logger
        self.auto_task_creation_enabled = True
        self.default_project_id = None  # Can be configured

    # Incident Management
    async def create_incident(self, db: Session, incident_data: IncidentCreate, creator_id: int) -> Incident:
        """Create a new incident"""
        try:
            incident = Incident(
                title=incident_data.title,
                description=incident_data.description,
                severity=incident_data.severity,
                source_system=incident_data.source_system,
                source_id=incident_data.source_id,
                alert_rule=incident_data.alert_rule,
                assigned_to=incident_data.assigned_to,
                created_by=creator_id,
                project_id=incident_data.project_id,
                started_at=incident_data.started_at or datetime.utcnow(),
                affected_services=incident_data.affected_services or [],
                affected_users_count=incident_data.affected_users_count or 0,
                metadata=incident_data.metadata or {},
                tags=incident_data.tags or []
            )
            
            db.add(incident)
            db.flush()  # Get the incident ID
            
            # Create initial update
            initial_update = IncidentUpdate(
                incident_id=incident.id,
                message=f"Инцидент создан: {incident.title}",
                update_type="created",
                new_status=IncidentStatus.OPEN,
                author_id=creator_id,
                is_public=True
            )
            db.add(initial_update)
            
            # Auto-create task if enabled and project specified
            if (self.auto_task_creation_enabled and 
                (incident_data.project_id or self.default_project_id)):
                
                project_id = incident_data.project_id or self.default_project_id
                task = await self._create_incident_task(db, incident, project_id, creator_id)
                if task:
                    incident.related_task_id = task.id
            
            db.commit()
            db.refresh(incident)
            
            self.logger.info(f"Created incident: {incident.title} (ID: {incident.id})")
            return incident
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating incident: {e}")
            raise

    async def get_incident(self, db: Session, incident_id: int) -> Optional[Incident]:
        """Get a specific incident with all related data"""
        return db.query(Incident).filter(Incident.id == incident_id).first()

    async def get_incidents(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[IncidentFilters] = None
    ) -> List[Incident]:
        """Get list of incidents with optional filtering"""
        query = db.query(Incident)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(Incident.status.in_(filters.status))
            if filters.severity:
                query = query.filter(Incident.severity.in_(filters.severity))
            if filters.assigned_to:
                query = query.filter(Incident.assigned_to == filters.assigned_to)
            if filters.project_id:
                query = query.filter(Incident.project_id == filters.project_id)
            if filters.source_system:
                query = query.filter(Incident.source_system.in_(filters.source_system))
            if filters.date_range:
                if filters.date_range.get('start'):
                    query = query.filter(Incident.started_at >= filters.date_range['start'])
                if filters.date_range.get('end'):
                    query = query.filter(Incident.started_at <= filters.date_range['end'])
        
        return query.order_by(desc(Incident.started_at)).offset(skip).limit(limit).all()

    async def update_incident(
        self, 
        db: Session, 
        incident_id: int, 
        incident_data: IncidentUpdateSchema,
        updater_id: int
    ) -> Optional[Incident]:
        """Update an existing incident"""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None
        
        old_status = incident.status
        
        # Update fields
        for field, value in incident_data.dict(exclude_unset=True).items():
            if field != 'update_message':  # Special field for update message
                setattr(incident, field, value)
        
        # Set resolution time if incident is resolved
        if (incident_data.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED] and 
            old_status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]):
            incident.resolved_at = datetime.utcnow()
            
            # Calculate downtime
            if incident.started_at:
                downtime = (incident.resolved_at - incident.started_at).total_seconds() / 60
                incident.downtime_minutes = downtime
        
        incident.updated_at = datetime.utcnow()
        
        # Create update record
        if incident_data.update_message or incident_data.status != old_status:
            update_message = incident_data.update_message or f"Статус изменен с {old_status.value} на {incident.status.value}"
            
            update_record = IncidentUpdate(
                incident_id=incident.id,
                message=update_message,
                update_type="status_change" if incident_data.status != old_status else "note",
                old_status=old_status if incident_data.status != old_status else None,
                new_status=incident.status if incident_data.status != old_status else None,
                author_id=updater_id,
                is_public=True
            )
            db.add(update_record)
        
        db.commit()
        db.refresh(incident)
        
        self.logger.info(f"Updated incident: {incident.title} (ID: {incident.id})")
        return incident

    # Alert Management
    async def create_alert(self, db: Session, alert_data: AlertCreate) -> MonitoringAlert:
        """Create a new monitoring alert"""
        try:
            alert = MonitoringAlert(
                name=alert_data.name,
                message=alert_data.message,
                severity=alert_data.severity,
                source_system=alert_data.source_system,
                rule_name=alert_data.rule_name,
                metric_name=alert_data.metric_name,
                current_value=alert_data.current_value,
                threshold_value=alert_data.threshold_value,
                started_at=alert_data.started_at or datetime.utcnow(),
                labels=alert_data.labels or {},
                annotations=alert_data.annotations or {}
            )
            
            db.add(alert)
            db.flush()  # Get the alert ID
            
            # Auto-create incident for critical alerts
            if alert_data.severity == IncidentSeverity.CRITICAL:
                incident = await self._create_alert_incident(db, alert)
                if incident:
                    alert.incident_id = incident.id
            
            # Auto-create task if enabled
            if self.auto_task_creation_enabled and self._should_create_task_for_alert(alert):
                task = await self._create_alert_task(db, alert)
                if task:
                    alert.auto_task_created = True
                    alert.created_task_id = task.id
            
            db.commit()
            db.refresh(alert)
            
            self.logger.info(f"Created alert: {alert.name} (ID: {alert.id})")
            return alert
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating alert: {e}")
            raise

    async def get_alerts(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[AlertFilters] = None
    ) -> List[MonitoringAlert]:
        """Get list of alerts with optional filtering"""
        query = db.query(MonitoringAlert)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(MonitoringAlert.status.in_(filters.status))
            if filters.severity:
                query = query.filter(MonitoringAlert.severity.in_(filters.severity))
            if filters.source_system:
                query = query.filter(MonitoringAlert.source_system.in_(filters.source_system))
            if filters.rule_name:
                query = query.filter(MonitoringAlert.rule_name.in_(filters.rule_name))
            if filters.has_incident is not None:
                if filters.has_incident:
                    query = query.filter(MonitoringAlert.incident_id.isnot(None))
                else:
                    query = query.filter(MonitoringAlert.incident_id.is_(None))
            if filters.date_range:
                if filters.date_range.get('start'):
                    query = query.filter(MonitoringAlert.started_at >= filters.date_range['start'])
                if filters.date_range.get('end'):
                    query = query.filter(MonitoringAlert.started_at <= filters.date_range['end'])
        
        return query.order_by(desc(MonitoringAlert.started_at)).offset(skip).limit(limit).all()

    # Operational Dashboard
    async def get_operational_dashboard(self, db: Session, period: str = "24h") -> OperationalDashboardResponse:
        """Get operational metrics dashboard data"""
        try:
            # Calculate date range
            end_time = datetime.utcnow()
            if period == "1h":
                start_time = end_time - timedelta(hours=1)
            elif period == "24h":
                start_time = end_time - timedelta(hours=24)
            elif period == "7d":
                start_time = end_time - timedelta(days=7)
            elif period == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # Get system metrics from unified monitoring service
            monitoring_data = unified_monitoring_service.get_dashboard_data()
            
            # Get incident statistics
            incident_stats = await self._get_incident_statistics(db, start_time, end_time)
            
            # Get alert statistics
            alert_stats = await self._get_alert_statistics(db, start_time, end_time)
            
            # Get service health metrics
            service_health = await self._get_service_health_metrics(db)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(db, start_time, end_time)
            
            # Get availability metrics
            availability_metrics = await self._get_availability_metrics(db, start_time, end_time)
            
            return OperationalDashboardResponse(
                period=period,
                start_time=start_time,
                end_time=end_time,
                system_metrics=monitoring_data.get("metrics", {}),
                incident_stats=incident_stats,
                alert_stats=alert_stats,
                service_health=service_health,
                performance_metrics=performance_metrics,
                availability_metrics=availability_metrics,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting operational dashboard: {e}")
            raise

    # Private helper methods
    async def _create_incident_task(
        self, 
        db: Session, 
        incident: Incident, 
        project_id: int, 
        creator_id: int
    ) -> Optional[Task]:
        """Create a task for an incident"""
        try:
            from ..schemas.project import TaskCreate
            
            # Determine task priority based on incident severity
            priority_mapping = {
                IncidentSeverity.LOW: TaskPriority.LOW,
                IncidentSeverity.MEDIUM: TaskPriority.MEDIUM,
                IncidentSeverity.HIGH: TaskPriority.HIGH,
                IncidentSeverity.CRITICAL: TaskPriority.CRITICAL
            }
            
            task_data = TaskCreate(
                title=f"[ИНЦИДЕНТ] {incident.title}",
                description=f"Автоматически созданная задача для инцидента #{incident.id}\n\n"
                           f"Описание инцидента: {incident.description or 'Не указано'}\n"
                           f"Серьезность: {incident.severity.value}\n"
                           f"Источник: {incident.source_system}\n"
                           f"Время начала: {incident.started_at}",
                type=TaskType.BUG,
                priority=priority_mapping.get(incident.severity, TaskPriority.MEDIUM),
                assignee_id=incident.assigned_to,
                reporter_id=creator_id,
                project_id=project_id,
                labels=[
                    "incident",
                    f"severity:{incident.severity.value}",
                    f"source:{incident.source_system}"
                ],
                custom_fields={
                    "incident_id": incident.id,
                    "incident_source": incident.source_system,
                    "incident_severity": incident.severity.value
                }
            )
            
            task = await project_service.create_task(db, task_data)
            self.logger.info(f"Created task {task.id} for incident {incident.id}")
            return task
            
        except Exception as e:
            self.logger.error(f"Error creating task for incident {incident.id}: {e}")
            return None

    async def _create_alert_incident(self, db: Session, alert: MonitoringAlert) -> Optional[Incident]:
        """Create an incident for a critical alert"""
        try:
            incident_data = IncidentCreate(
                title=f"Критический алерт: {alert.name}",
                description=f"Автоматически созданный инцидент для критического алерта\n\n"
                           f"Алерт: {alert.message}\n"
                           f"Правило: {alert.rule_name}\n"
                           f"Метрика: {alert.metric_name}\n"
                           f"Текущее значение: {alert.current_value}\n"
                           f"Пороговое значение: {alert.threshold_value}",
                severity=alert.severity,
                source_system=alert.source_system,
                source_id=str(alert.id),
                alert_rule=alert.rule_name,
                project_id=self.default_project_id,
                started_at=alert.started_at,
                metadata={
                    "alert_id": alert.id,
                    "alert_labels": alert.labels,
                    "alert_annotations": alert.annotations
                },
                tags=["auto-created", "alert-incident"]
            )
            
            # Use system user as creator (ID 1) or first admin
            system_user = db.query(User).filter(User.is_admin == True).first()
            if not system_user:
                self.logger.warning("No admin user found for auto-incident creation")
                return None
            
            incident = await self.create_incident(db, incident_data, system_user.id)
            self.logger.info(f"Created incident {incident.id} for alert {alert.id}")
            return incident
            
        except Exception as e:
            self.logger.error(f"Error creating incident for alert {alert.id}: {e}")
            return None

    async def _create_alert_task(self, db: Session, alert: MonitoringAlert) -> Optional[Task]:
        """Create a task for an alert"""
        try:
            from ..schemas.project import TaskCreate
            
            # Only create tasks for certain alert types
            if not self._should_create_task_for_alert(alert):
                return None
            
            # Determine task priority based on alert severity
            priority_mapping = {
                IncidentSeverity.LOW: TaskPriority.LOW,
                IncidentSeverity.MEDIUM: TaskPriority.MEDIUM,
                IncidentSeverity.HIGH: TaskPriority.HIGH,
                IncidentSeverity.CRITICAL: TaskPriority.CRITICAL
            }
            
            # Use system user as creator
            system_user = db.query(User).filter(User.is_admin == True).first()
            if not system_user:
                return None
            
            task_data = TaskCreate(
                title=f"[АЛЕРТ] {alert.name}",
                description=f"Автоматически созданная задача для алерта\n\n"
                           f"Сообщение: {alert.message}\n"
                           f"Правило: {alert.rule_name}\n"
                           f"Метрика: {alert.metric_name}\n"
                           f"Текущее значение: {alert.current_value}\n"
                           f"Пороговое значение: {alert.threshold_value}",
                type=TaskType.MAINTENANCE,
                priority=priority_mapping.get(alert.severity, TaskPriority.MEDIUM),
                reporter_id=system_user.id,
                project_id=self.default_project_id,
                labels=[
                    "alert",
                    f"severity:{alert.severity.value}",
                    f"rule:{alert.rule_name}"
                ],
                custom_fields={
                    "alert_id": alert.id,
                    "alert_rule": alert.rule_name,
                    "alert_severity": alert.severity.value
                }
            )
            
            task = await project_service.create_task(db, task_data)
            self.logger.info(f"Created task {task.id} for alert {alert.id}")
            return task
            
        except Exception as e:
            self.logger.error(f"Error creating task for alert {alert.id}: {e}")
            return None

    def _should_create_task_for_alert(self, alert: MonitoringAlert) -> bool:
        """Determine if a task should be created for an alert"""
        # Create tasks for high and critical alerts
        if alert.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            return True
        
        # Create tasks for specific alert rules
        task_creation_rules = [
            "high_error_rate",
            "service_unhealthy",
            "high_memory_usage",
            "disk_space_low"
        ]
        
        return alert.rule_name in task_creation_rules

    async def _get_incident_statistics(self, db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get incident statistics for the dashboard"""
        # Total incidents in period
        total_incidents = db.query(Incident).filter(
            and_(
                Incident.started_at >= start_time,
                Incident.started_at <= end_time
            )
        ).count()
        
        # Open incidents
        open_incidents = db.query(Incident).filter(
            Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.IDENTIFIED])
        ).count()
        
        # Resolved incidents in period
        resolved_incidents = db.query(Incident).filter(
            and_(
                Incident.resolved_at >= start_time,
                Incident.resolved_at <= end_time
            )
        ).count()
        
        # Average resolution time
        avg_resolution_query = db.query(
            func.avg(
                func.extract('epoch', Incident.resolved_at - Incident.started_at) / 60
            )
        ).filter(
            and_(
                Incident.resolved_at >= start_time,
                Incident.resolved_at <= end_time,
                Incident.resolved_at.isnot(None)
            )
        ).scalar()
        
        avg_resolution_time = avg_resolution_query or 0
        
        # Incidents by severity
        severity_counts = {}
        for severity in IncidentSeverity:
            count = db.query(Incident).filter(
                and_(
                    Incident.started_at >= start_time,
                    Incident.started_at <= end_time,
                    Incident.severity == severity
                )
            ).count()
            severity_counts[severity.value] = count
        
        return {
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "resolved_incidents": resolved_incidents,
            "avg_resolution_time_minutes": round(avg_resolution_time, 2),
            "incidents_by_severity": severity_counts
        }

    async def _get_alert_statistics(self, db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get alert statistics for the dashboard"""
        # Total alerts in period
        total_alerts = db.query(MonitoringAlert).filter(
            and_(
                MonitoringAlert.started_at >= start_time,
                MonitoringAlert.started_at <= end_time
            )
        ).count()
        
        # Active alerts
        active_alerts = db.query(MonitoringAlert).filter(
            MonitoringAlert.status == AlertStatus.ACTIVE
        ).count()
        
        # Auto-created tasks
        auto_tasks = db.query(MonitoringAlert).filter(
            and_(
                MonitoringAlert.started_at >= start_time,
                MonitoringAlert.started_at <= end_time,
                MonitoringAlert.auto_task_created == True
            )
        ).count()
        
        # Alerts by severity
        severity_counts = {}
        for severity in IncidentSeverity:
            count = db.query(MonitoringAlert).filter(
                and_(
                    MonitoringAlert.started_at >= start_time,
                    MonitoringAlert.started_at <= end_time,
                    MonitoringAlert.severity == severity
                )
            ).count()
            severity_counts[severity.value] = count
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "auto_created_tasks": auto_tasks,
            "alerts_by_severity": severity_counts
        }

    async def _get_service_health_metrics(self, db: Session) -> Dict[str, Any]:
        """Get service health metrics"""
        # Get data from unified monitoring service
        monitoring_data = unified_monitoring_service.get_dashboard_data()
        
        return {
            "total_services": monitoring_data.get("services", {}).get("total", 0),
            "healthy_services": monitoring_data.get("services", {}).get("healthy", 0),
            "degraded_services": monitoring_data.get("services", {}).get("degraded", 0),
            "unhealthy_services": monitoring_data.get("services", {}).get("unhealthy", 0),
            "overall_health_score": monitoring_data.get("metrics", {}).get("service_health_score", 0)
        }

    async def _get_performance_metrics(self, db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get performance metrics"""
        # Get data from unified monitoring service
        monitoring_data = unified_monitoring_service.get_dashboard_data()
        
        return {
            "avg_response_time": monitoring_data.get("metrics", {}).get("llm_average_response_time", 0),
            "p95_response_time": monitoring_data.get("metrics", {}).get("llm_p95_response_time", 0),
            "requests_per_minute": monitoring_data.get("metrics", {}).get("llm_requests_per_minute", 0),
            "error_rate": monitoring_data.get("metrics", {}).get("llm_error_rate", 0),
            "cpu_usage": monitoring_data.get("metrics", {}).get("system_cpu_usage_percent", 0),
            "memory_usage": monitoring_data.get("metrics", {}).get("system_memory_usage_percent", 0)
        }

    async def _get_availability_metrics(self, db: Session, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get availability metrics"""
        # Calculate uptime based on incidents
        total_minutes = (end_time - start_time).total_seconds() / 60
        
        # Get total downtime from resolved incidents
        downtime_query = db.query(
            func.sum(Incident.downtime_minutes)
        ).filter(
            and_(
                Incident.resolved_at >= start_time,
                Incident.resolved_at <= end_time,
                Incident.downtime_minutes > 0
            )
        ).scalar()
        
        total_downtime = downtime_query or 0
        uptime_percentage = ((total_minutes - total_downtime) / total_minutes * 100) if total_minutes > 0 else 100
        
        return {
            "uptime_percentage": round(uptime_percentage, 3),
            "total_downtime_minutes": round(total_downtime, 2),
            "mttr_minutes": 0,  # Mean Time To Recovery - would need more complex calculation
            "mtbf_hours": 0     # Mean Time Between Failures - would need more complex calculation
        }


# Global service instance
monitoring_integration_service = MonitoringIntegrationService()