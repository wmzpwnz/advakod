from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

from ..models.project import (
    ProjectStatus, ProjectType, ProjectVisibility, ProjectHealth,
    TaskStatus, TaskType, TaskPriority,
    MilestoneStatus, SprintStatus
)


# Base schemas
class ProjectMemberBase(BaseModel):
    user_id: int
    role: str = Field(..., min_length=1, max_length=50)
    allocation: float = Field(100.0, ge=0, le=100)
    is_active: bool = True


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    allocation: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class ProjectMemberResponse(ProjectMemberBase):
    id: int
    project_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    key: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z][A-Z0-9]*$")
    type: ProjectType = ProjectType.SOFTWARE
    visibility: ProjectVisibility = ProjectVisibility.TEAM
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    currency: str = Field("RUB", min_length=3, max_length=3)


class ProjectCreate(ProjectBase):
    lead_id: int
    members: Optional[List[ProjectMemberCreate]] = []

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[ProjectType] = None
    visibility: Optional[ProjectVisibility] = None
    status: Optional[ProjectStatus] = None
    health: Optional[ProjectHealth] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    health: ProjectHealth
    lead_id: int
    lead_name: Optional[str] = None
    progress: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    spent_budget: float = 0.0
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    members: List[ProjectMemberResponse] = []

    class Config:
        from_attributes = True


# Task schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: TaskType = TaskType.FEATURE
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    milestone_id: Optional[int] = None
    sprint_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    story_points: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    labels: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    reporter_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    milestone_id: Optional[int] = None
    sprint_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    story_points: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    reporter_id: int
    reporter_name: Optional[str] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None
    milestone_name: Optional[str] = None
    sprint_name: Optional[str] = None
    actual_hours: float = 0.0
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Task comment schemas
class TaskCommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class TaskCommentCreate(TaskCommentBase):
    task_id: int


class TaskCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class TaskCommentResponse(TaskCommentBase):
    id: int
    task_id: int
    author_id: int
    author_name: Optional[str] = None
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Milestone schemas
class MilestoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[int] = None
    start_date: datetime
    due_date: datetime
    budget: Optional[float] = Field(None, ge=0)
    currency: str = Field("RUB", min_length=3, max_length=3)

    @validator('due_date')
    def due_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('Due date must be after start date')
        return v


class MilestoneCreate(MilestoneBase):
    owner_id: int


class MilestoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)


class MilestoneResponse(MilestoneBase):
    id: int
    status: MilestoneStatus
    owner_id: int
    owner_name: Optional[str] = None
    project_name: Optional[str] = None
    progress: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    total_story_points: Optional[int] = None
    completed_story_points: int = 0
    spent_budget: float = 0.0
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sprint schemas
class SprintBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    goal: Optional[str] = None
    project_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    capacity: int = Field(..., ge=0)

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    goal: Optional[str] = None
    status: Optional[SprintStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=0)
    commitment: Optional[int] = Field(None, ge=0)
    completed: Optional[int] = Field(None, ge=0)
    velocity: Optional[float] = Field(None, ge=0)


class SprintResponse(SprintBase):
    id: int
    status: SprintStatus
    project_name: Optional[str] = None
    commitment: int = 0
    completed: int = 0
    velocity: float = 0.0
    burndown_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Time entry schemas
class TimeEntryBase(BaseModel):
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    description: str = Field(..., min_length=1)
    hours: float = Field(..., gt=0, le=24)
    date: datetime
    billable: bool = True
    hourly_rate: Optional[float] = Field(None, ge=0)
    currency: str = Field("RUB", min_length=3, max_length=3)


class TimeEntryCreate(TimeEntryBase):
    pass


class TimeEntryUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    hours: Optional[float] = Field(None, gt=0, le=24)
    date: Optional[datetime] = None
    billable: Optional[bool] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    status: Optional[str] = None


class TimeEntryResponse(TimeEntryBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    task_title: Optional[str] = None
    project_name: Optional[str] = None
    status: str = "draft"
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dashboard and analytics schemas
class ProjectDashboardStats(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    overdue_tasks: int = 0
    total_team_members: int = 0
    average_project_health: float = 0.0
    budget_utilization: float = 0.0


class VelocityPoint(BaseModel):
    sprint_name: str
    planned: int
    completed: int
    date: datetime


class ResourceUtilization(BaseModel):
    user_id: int
    user_name: str
    total_capacity: float
    allocated: float
    utilization: float
    overallocated: bool = False


class ProjectActivity(BaseModel):
    id: int
    type: str
    description: str
    user_id: int
    user_name: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None
    created_at: datetime


class UpcomingDeadline(BaseModel):
    id: int
    name: str
    type: str  # milestone, task, sprint
    due_date: datetime
    progress: float
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    priority: Optional[str] = None


class ProjectDashboardResponse(BaseModel):
    stats: ProjectDashboardStats
    velocity_trend: List[VelocityPoint] = []
    resource_utilization: List[ResourceUtilization] = []
    upcoming_deadlines: List[UpcomingDeadline] = []
    recent_activity: List[ProjectActivity] = []
    period: str = "30d"
    last_updated: datetime


# Calendar and events schemas
class CalendarEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str  # milestone, deadline, sprint, meeting, task
    date: datetime
    time: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[int] = None
    priority: Optional[str] = None
    assignees: Optional[List[Dict[str, Any]]] = []


class CalendarEventsResponse(BaseModel):
    events: List[CalendarEvent]
    view: str = "month"
    date: datetime


# KPI and metrics schemas
class KPIMetric(BaseModel):
    id: str
    title: str
    value: float
    target: Optional[float] = None
    trend: float = 0.0
    type: str = "number"  # number, percentage, currency, hours, days
    description: str
    health_status: str = "neutral"  # good, warning, critical, neutral


class ProjectKPIResponse(BaseModel):
    velocity: Optional[Dict[str, Any]] = None
    budget: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None
    delivery: Optional[Dict[str, Any]] = None
    quality: Optional[Dict[str, Any]] = None
    cycle_time: Optional[Dict[str, Any]] = None
    period: str = "30d"
    last_updated: datetime


# Filters and search schemas
class ProjectFilters(BaseModel):
    status: Optional[List[ProjectStatus]] = None
    type: Optional[List[ProjectType]] = None
    health: Optional[List[ProjectHealth]] = None
    lead_id: Optional[int] = None
    member_id: Optional[int] = None
    date_range: Optional[Dict[str, datetime]] = None


class TaskFilters(BaseModel):
    status: Optional[List[TaskStatus]] = None
    type: Optional[List[TaskType]] = None
    priority: Optional[List[TaskPriority]] = None
    assignee_id: Optional[int] = None
    reporter_id: Optional[int] = None
    project_id: Optional[int] = None
    milestone_id: Optional[int] = None
    sprint_id: Optional[int] = None
    labels: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None


# Bulk operations schemas
class BulkTaskUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_items=1)
    updates: TaskUpdate


class BulkTaskStatusUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_items=1)
    status: TaskStatus


class BulkTaskAssignment(BaseModel):
    task_ids: List[int] = Field(..., min_items=1)
    assignee_id: Optional[int] = None


# Export schemas
class ProjectExportRequest(BaseModel):
    project_ids: Optional[List[int]] = None
    include_tasks: bool = True
    include_time_entries: bool = False
    include_comments: bool = False
    date_range: Optional[Dict[str, datetime]] = None
    format: str = Field("csv", pattern="^(csv|json|xlsx)$")


class ProjectExportResponse(BaseModel):
    export_id: str
    status: str
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: datetime


# API Response wrapper
class ProjectApiResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    pagination: Optional[Dict[str, int]] = None