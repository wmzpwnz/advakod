"""
Schemas for monitoring system integration
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from ..models.monitoring_integration import (
    IncidentStatus, IncidentSeverity, AlertStatus
)


# Base schemas
class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source_system: str = Field(..., min_length=1, max_length=100)
    source_id: Optional[str] = Field(None, max_length=255)
    alert_rule: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[int] = None
    project_id: Optional[int] = None
    started_at: Optional[datetime] = None
    affected_services: Optional[List[str]] = []
    affected_users_count: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[int] = None
    project_id: Optional[int] = None
    affected_services: Optional[List[str]] = None
    affected_users_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    update_message: Optional[str] = None  # Message for the update log


class IncidentResponse(IncidentBase):
    id: int
    status: IncidentStatus
    created_by: int
    related_task_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    downtime_minutes: float = 0.0
    created_at: datetime
    updated_at: datetime
    
    # Related data
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
    project_name: Optional[str] = None
    related_task_title: Optional[str] = None
    alerts_count: Optional[int] = 0
    updates_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Alert schemas
class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source_system: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=255)
    metric_name: Optional[str] = Field(None, max_length=255)
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    started_at: Optional[datetime] = None
    labels: Optional[Dict[str, str]] = {}
    annotations: Optional[Dict[str, str]] = {}


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    incident_id: Optional[int] = None
    auto_task_created: bool = False
    created_task_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    incident_title: Optional[str] = None
    created_task_title: Optional[str] = None

    class Config:
        from_attributes = True


# Incident Update schemas
class IncidentUpdateBase(BaseModel):
    message: str = Field(..., min_length=1)
    update_type: str = Field(..., min_length=1, max_length=50)
    is_public: bool = True


class IncidentUpdateCreate(IncidentUpdateBase):
    incident_id: int


class IncidentUpdateResponse(IncidentUpdateBase):
    id: int
    incident_id: int
    old_status: Optional[IncidentStatus] = None
    new_status: Optional[IncidentStatus] = None
    author_id: int
    author_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Operational Metrics schemas
class MetricResponse(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    value: float
    unit: Optional[str] = None
    category: str
    chart_type: str
    color: Optional[str] = None
    timestamp: datetime
    
    # Threshold status
    status: str = "normal"  # normal, warning, critical
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None


class OperationalDashboardResponse(BaseModel):
    period: str
    start_time: datetime
    end_time: datetime
    last_updated: datetime
    
    # System metrics from monitoring service
    system_metrics: Dict[str, float]
    
    # Incident statistics
    incident_stats: Dict[str, Any]
    
    # Alert statistics
    alert_stats: Dict[str, Any]
    
    # Service health
    service_health: Dict[str, Any]
    
    # Performance metrics
    performance_metrics: Dict[str, Any]
    
    # Availability metrics
    availability_metrics: Dict[str, Any]


# Filter schemas
class IncidentFilters(BaseModel):
    status: Optional[List[IncidentStatus]] = None
    severity: Optional[List[IncidentSeverity]] = None
    assigned_to: Optional[int] = None
    project_id: Optional[int] = None
    source_system: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None


class AlertFilters(BaseModel):
    status: Optional[List[AlertStatus]] = None
    severity: Optional[List[IncidentSeverity]] = None
    source_system: Optional[List[str]] = None
    rule_name: Optional[List[str]] = None
    has_incident: Optional[bool] = None
    date_range: Optional[Dict[str, datetime]] = None


# Webhook schemas for external systems
class PrometheusAlert(BaseModel):
    """Schema for Prometheus AlertManager webhook"""
    status: str  # firing, resolved
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: datetime
    endsAt: Optional[datetime] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class PrometheusWebhook(BaseModel):
    """Schema for Prometheus AlertManager webhook payload"""
    receiver: str
    status: str
    alerts: List[PrometheusAlert]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    version: str
    groupKey: str
    truncatedAlerts: Optional[int] = 0


# Task integration schemas
class TaskFromIncident(BaseModel):
    """Schema for creating a task from an incident"""
    incident_id: int
    project_id: int
    assignee_id: Optional[int] = None
    additional_description: Optional[str] = None


class TaskFromAlert(BaseModel):
    """Schema for creating a task from an alert"""
    alert_id: int
    project_id: int
    assignee_id: Optional[int] = None
    additional_description: Optional[str] = None


# Statistics schemas
class IncidentStatistics(BaseModel):
    total_incidents: int
    open_incidents: int
    resolved_incidents: int
    avg_resolution_time_minutes: float
    incidents_by_severity: Dict[str, int]
    incidents_by_status: Dict[str, int]
    mttr_minutes: Optional[float] = None  # Mean Time To Recovery
    mtbf_hours: Optional[float] = None    # Mean Time Between Failures


class AlertStatistics(BaseModel):
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    auto_created_tasks: int
    alerts_by_severity: Dict[str, int]
    alerts_by_rule: Dict[str, int]
    false_positive_rate: Optional[float] = None


# Configuration schemas
class MonitoringIntegrationConfig(BaseModel):
    """Configuration for monitoring integration"""
    auto_task_creation_enabled: bool = True
    default_project_id: Optional[int] = None
    task_creation_rules: List[str] = []
    incident_auto_assignment: bool = False
    alert_grouping_enabled: bool = True
    notification_channels: List[str] = []