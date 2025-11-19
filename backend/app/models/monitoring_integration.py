"""
Models for monitoring system integration with project management
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base


class IncidentStatus(PyEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(PyEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class Incident(Base):
    """Инцидент системы мониторинга"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Incident classification
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)
    
    # Source information
    source_system = Column(String(100), nullable=False)  # monitoring, alertmanager, manual
    source_id = Column(String(255), nullable=True)  # External system ID
    alert_rule = Column(String(255), nullable=True)  # Alert rule name
    
    # Assignment and ownership
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Project integration
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Impact and metrics
    affected_services = Column(JSON)  # List of affected services
    affected_users_count = Column(Integer, nullable=False, default=0)
    downtime_minutes = Column(Float, nullable=False, default=0.0)
    
    # Additional data
    incident_metadata = Column(JSON)  # Additional incident data
    tags = Column(JSON)  # List of tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    project = relationship("Project", foreign_keys=[project_id])
    related_task = relationship("Task", foreign_keys=[related_task_id])
    alerts = relationship("MonitoringAlert", back_populates="incident")
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Incident(id={self.id}, title='{self.title}', severity='{self.severity}')>"


class MonitoringAlert(Base):
    """Алерт системы мониторинга"""
    __tablename__ = "monitoring_alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    # Alert classification
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    
    # Source information
    source_system = Column(String(100), nullable=False)  # prometheus, grafana, custom
    rule_name = Column(String(255), nullable=False)
    metric_name = Column(String(255), nullable=True)
    current_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    
    # Incident relationship
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    
    # Auto-task creation
    auto_task_created = Column(Boolean, nullable=False, default=False)
    created_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Labels and metadata
    labels = Column(JSON)  # Prometheus-style labels
    annotations = Column(JSON)  # Additional annotations
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    incident = relationship("Incident", back_populates="alerts")
    created_task = relationship("Task", foreign_keys=[created_task_id])

    def __repr__(self):
        return f"<MonitoringAlert(id={self.id}, name='{self.name}', severity='{self.severity}')>"


class IncidentUpdate(Base):
    """Обновление инцидента"""
    __tablename__ = "incident_updates"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    # Update content
    message = Column(Text, nullable=False)
    update_type = Column(String(50), nullable=False)  # status_change, investigation, resolution, note
    
    # Status changes
    old_status = Column(Enum(IncidentStatus), nullable=True)
    new_status = Column(Enum(IncidentStatus), nullable=True)
    
    # Author
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Visibility
    is_public = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    incident = relationship("Incident", back_populates="updates")
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<IncidentUpdate(id={self.id}, incident_id={self.incident_id}, type='{self.update_type}')>"


class OperationalMetric(Base):
    """Операционная метрика для дашборда"""
    __tablename__ = "operational_metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Metric configuration
    metric_type = Column(String(50), nullable=False)  # gauge, counter, histogram, summary
    unit = Column(String(20), nullable=True)  # seconds, bytes, percent, count
    category = Column(String(100), nullable=False)  # system, application, business
    
    # Data source
    source_system = Column(String(100), nullable=False)  # prometheus, database, api
    query = Column(Text, nullable=False)  # Query to get metric value
    
    # Display configuration
    chart_type = Column(String(50), nullable=False, default='line')  # line, bar, gauge, number
    color = Column(String(7), nullable=True)  # Hex color
    order_index = Column(Integer, nullable=False, default=0)
    
    # Thresholds for alerting
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OperationalMetric(id={self.id}, name='{self.name}', category='{self.category}')>"


class MetricValue(Base):
    """Значение операционной метрики"""
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("operational_metrics.id"), nullable=False)
    
    # Value data
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Additional context
    labels = Column(JSON)  # Additional labels/dimensions
    
    # Relationships
    metric = relationship("OperationalMetric", foreign_keys=[metric_id])

    def __repr__(self):
        return f"<MetricValue(metric_id={self.metric_id}, value={self.value}, timestamp={self.timestamp})>"