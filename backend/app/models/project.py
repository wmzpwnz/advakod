from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base


class ProjectStatus(PyEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectType(PyEnum):
    SOFTWARE = "software"
    MARKETING = "marketing"
    RESEARCH = "research"
    OPERATIONS = "operations"


class ProjectVisibility(PyEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM = "team"


class TaskStatus(PyEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskType(PyEnum):
    FEATURE = "feature"
    BUG = "bug"
    IMPROVEMENT = "improvement"
    MAINTENANCE = "maintenance"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"


class TaskPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MilestoneStatus(PyEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class SprintStatus(PyEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectHealth(PyEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    key = Column(String(10), nullable=False, unique=True, index=True)  # Project key like "ADV"
    
    # Project configuration
    type = Column(Enum(ProjectType), nullable=False, default=ProjectType.SOFTWARE)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    visibility = Column(Enum(ProjectVisibility), nullable=False, default=ProjectVisibility.TEAM)
    health = Column(Enum(ProjectHealth), nullable=False, default=ProjectHealth.GREEN)
    
    # Project leadership
    lead_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Budget
    budget = Column(Float, nullable=True)
    spent_budget = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default='RUB')
    
    # Progress tracking
    progress = Column(Float, nullable=False, default=0.0)  # 0-100
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    
    # Metadata
    settings = Column(JSON)  # Project-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lead = relationship("User", foreign_keys=[lead_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', key='{self.key}')>"


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(50), nullable=False, default='developer')  # owner, admin, developer, designer, tester, viewer
    allocation = Column(Float, nullable=False, default=100.0)  # Percentage of time allocated
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Task classification
    type = Column(Enum(TaskType), nullable=False, default=TaskType.FEATURE)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.BACKLOG)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    
    # Assignment
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Project relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    
    # Task hierarchy
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Estimation and tracking
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=False, default=0.0)
    story_points = Column(Integer, nullable=True)
    
    # Timeline
    due_date = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    labels = Column(JSON)  # List of labels/tags
    custom_fields = Column(JSON)  # Custom field values
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    project = relationship("Project", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id])
    subtasks = relationship("Task", back_populates="parent_task")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task")
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<TaskComment(id={self.id}, task_id={self.task_id})>"


class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<TaskAttachment(id={self.id}, file_name='{self.file_name}')>"


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    type = Column(String(50), nullable=False, default='blocks')  # blocks, relates_to, duplicates, caused_by
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id])

    def __repr__(self):
        return f"<TaskDependency(task_id={self.task_id}, depends_on={self.depends_on_task_id})>"


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Status and timeline
    status = Column(Enum(MilestoneStatus), nullable=False, default=MilestoneStatus.PLANNING)
    start_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    progress = Column(Float, nullable=False, default=0.0)  # 0-100
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    total_story_points = Column(Integer, nullable=True)
    completed_story_points = Column(Integer, nullable=False, default=0)
    
    # Budget
    budget = Column(Float, nullable=True)
    spent_budget = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default='RUB')
    
    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
    owner = relationship("User", foreign_keys=[owner_id])
    tasks = relationship("Task", back_populates="milestone")

    def __repr__(self):
        return f"<Milestone(id={self.id}, name='{self.name}', status='{self.status}')>"


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    goal = Column(Text)
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Status and timeline
    status = Column(Enum(SprintStatus), nullable=False, default=SprintStatus.PLANNING)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Capacity and commitment
    capacity = Column(Integer, nullable=False)  # Story points or hours
    commitment = Column(Integer, nullable=False, default=0)  # Planned story points or hours
    completed = Column(Integer, nullable=False, default=0)  # Actual completed story points or hours
    velocity = Column(Float, nullable=False, default=0.0)  # Average velocity from previous sprints
    
    # Burndown data
    burndown_data = Column(JSON)  # Daily burndown points
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")

    def __repr__(self):
        return f"<Sprint(id={self.id}, name='{self.name}', status='{self.status}')>"


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Work item relationships
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Time tracking
    description = Column(Text, nullable=False)
    hours = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Billing
    billable = Column(Boolean, nullable=False, default=True)
    hourly_rate = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default='RUB')
    
    # Approval workflow
    status = Column(String(20), nullable=False, default='draft')  # draft, submitted, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, user_id={self.user_id}, hours={self.hours})>"


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Capacity
    total_capacity = Column(Float, nullable=False, default=40.0)  # Hours per week
    
    # User information
    role = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    hourly_rate = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default='RUB')
    
    # Skills and capabilities
    skills = Column(JSON)  # List of skills with levels
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    allocations = relationship("ProjectAllocation", back_populates="resource")
    availability = relationship("AvailabilityPeriod", back_populates="resource")

    def __repr__(self):
        return f"<ResourceAllocation(id={self.id}, user_id={self.user_id})>"


class ProjectAllocation(Base):
    __tablename__ = "project_allocations"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resource_allocations.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Allocation details
    allocation = Column(Float, nullable=False)  # Percentage or hours
    role = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    resource = relationship("ResourceAllocation", back_populates="allocations")
    project = relationship("Project", foreign_keys=[project_id])

    def __repr__(self):
        return f"<ProjectAllocation(resource_id={self.resource_id}, project_id={self.project_id})>"


class AvailabilityPeriod(Base):
    __tablename__ = "availability_periods"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resource_allocations.id"), nullable=False)
    
    # Availability details
    type = Column(String(50), nullable=False)  # vacation, sick_leave, training, conference, unavailable
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    
    # Approval
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    resource = relationship("ResourceAllocation", back_populates="availability")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<AvailabilityPeriod(id={self.id}, type='{self.type}')>"