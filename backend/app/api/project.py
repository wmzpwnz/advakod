from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_admin_user, get_current_user
from ..models.user import User
from ..models.project import ProjectStatus, TaskStatus, MilestoneStatus, SprintStatus
from ..schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectFilters,
    TaskCreate, TaskUpdate, TaskResponse, TaskFilters,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
    SprintCreate, SprintUpdate, SprintResponse,
    TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse,
    ProjectDashboardResponse, CalendarEventsResponse, ProjectKPIResponse,
    BulkTaskUpdate, BulkTaskStatusUpdate, BulkTaskAssignment,
    ProjectExportRequest, ProjectExportResponse
)
from ..services.project_service import project_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Dashboard Endpoints
@router.get("/dashboard", response_model=ProjectDashboardResponse)
async def get_project_dashboard(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get project management dashboard data"""
    try:
        dashboard_data = await project_service.get_dashboard_data(db, period)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.get("/kpi", response_model=ProjectKPIResponse)
async def get_project_kpi(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get project KPI metrics"""
    try:
        # This would be implemented in the service
        # For now, return mock data
        from datetime import datetime
        return ProjectKPIResponse(
            velocity={"current": 25, "target": 30, "trend": 5.2},
            budget={"utilization": 78.5, "trend": -2.1},
            team={"utilization": 85.2, "trend": 1.8},
            delivery={"onTime": 92.3, "trend": 3.5},
            quality={"score": 8.7, "trend": 0.8},
            cycle_time={"average": 5.2, "target": 4.5, "trend": -8.3},
            period=period,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error getting KPI data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get KPI data")


# Calendar Endpoints
@router.get("/calendar/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    date: str = Query(..., description="Date in ISO format"),
    view: str = Query("month", pattern="^(month|week|day)$"),
    types: Optional[str] = Query(None, description="Comma-separated event types"),
    priorities: Optional[str] = Query(None, description="Comma-separated priorities"),
    projects: Optional[str] = Query(None, description="Comma-separated project IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get calendar events for project management"""
    try:
        from datetime import datetime
        from ..schemas.project import CalendarEvent
        
        # Mock calendar events - in real implementation, this would query the database
        events = [
            CalendarEvent(
                id="1",
                title="Sprint Planning",
                description="Plan next sprint goals and tasks",
                type="meeting",
                date=datetime.utcnow(),
                time="10:00",
                project="ADVAKOD",
                project_id=1,
                priority="high"
            ),
            CalendarEvent(
                id="2",
                title="Release v2.0",
                description="Major release milestone",
                type="milestone",
                date=datetime.utcnow(),
                project="ADVAKOD",
                project_id=1,
                priority="critical"
            )
        ]
        
        return CalendarEventsResponse(
            events=events,
            view=view,
            date=datetime.fromisoformat(date.replace('Z', '+00:00'))
        )
    except Exception as e:
        logger.error(f"Error getting calendar events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calendar events")


# Project Management Endpoints
@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[List[ProjectStatus]] = Query(None),
    type: Optional[List[str]] = Query(None),
    health: Optional[List[str]] = Query(None),
    lead_id: Optional[int] = Query(None),
    member_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of projects with optional filtering"""
    try:
        filters = ProjectFilters(
            status=status,
            lead_id=lead_id,
            member_id=member_id
        )
        
        projects = await project_service.get_projects(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters,
            user_id=current_user.id
        )
        return projects
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get projects")


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project"""
    try:
        project = await project_service.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new project"""
    try:
        project = await project_service.create_project(db, project_data, current_user.id)
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing project"""
    try:
        project = await project_service.update_project(db, project_id, project_data)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a project"""
    try:
        success = await project_service.delete_project(db, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


# Task Management Endpoints
@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[List[TaskStatus]] = Query(None),
    type: Optional[List[str]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    assignee_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    milestone_id: Optional[int] = Query(None),
    sprint_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of tasks with optional filtering"""
    try:
        filters = TaskFilters(
            status=status,
            assignee_id=assignee_id,
            project_id=project_id,
            milestone_id=milestone_id,
            sprint_id=sprint_id
        )
        
        tasks = await project_service.get_tasks(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters
        )
        return tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tasks")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task"""
    try:
        task = await project_service.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task")


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    try:
        # Set reporter to current user if not specified
        if not task_data.reporter_id:
            task_data.reporter_id = current_user.id
            
        task = await project_service.create_task(db, task_data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing task"""
    try:
        task = await project_service.update_task(db, task_id, task_data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    try:
        success = await project_service.delete_task(db, task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


# Bulk Task Operations
@router.patch("/tasks/bulk/update")
async def bulk_update_tasks(
    bulk_update: BulkTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update multiple tasks at once"""
    try:
        results = []
        errors = []
        
        for task_id in bulk_update.task_ids:
            try:
                task = await project_service.update_task(db, task_id, bulk_update.updates)
                if task:
                    results.append({"task_id": task_id, "status": "updated"})
                else:
                    errors.append({"task_id": task_id, "error": "Task not found"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})
        
        return {
            "updated": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
    except Exception as e:
        logger.error(f"Error in bulk task update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tasks")


@router.patch("/tasks/bulk/status")
async def bulk_update_task_status(
    bulk_update: BulkTaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update status of multiple tasks"""
    try:
        from ..schemas.project import TaskUpdate
        
        task_update = TaskUpdate(status=bulk_update.status)
        results = []
        errors = []
        
        for task_id in bulk_update.task_ids:
            try:
                task = await project_service.update_task(db, task_id, task_update)
                if task:
                    results.append({"task_id": task_id, "status": "updated"})
                else:
                    errors.append({"task_id": task_id, "error": "Task not found"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})
        
        return {
            "updated": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
    except Exception as e:
        logger.error(f"Error in bulk status update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task statuses")


# Export Endpoints
@router.post("/export", response_model=ProjectExportResponse)
async def export_project_data(
    export_request: ProjectExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Export project data in various formats"""
    try:
        # For now, return a placeholder response
        # In a real implementation, this would generate the export file
        import uuid
        from datetime import datetime, timedelta
        
        export_id = str(uuid.uuid4())
        
        # Add background task to generate export
        # background_tasks.add_task(generate_project_export, export_request, export_id)
        
        return ProjectExportResponse(
            export_id=export_id,
            status="processing",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
    except Exception as e:
        logger.error(f"Error exporting project data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export project data")
# Kanban Board Endpoints
@router.get("/kanban")
async def get_kanban_board(
    project_id: Optional[int] = Query(None),
    sprint_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get kanban board data with columns and tasks"""
    try:
        # Define default columns
        default_columns = [
            {
                "id": "backlog",
                "name": "Бэклог",
                "status": "backlog",
                "color": "gray",
                "order": 0,
                "wip_limit": None,
                "tasks": []
            },
            {
                "id": "todo",
                "name": "К выполнению", 
                "status": "todo",
                "color": "blue",
                "order": 1,
                "wip_limit": 5,
                "tasks": []
            },
            {
                "id": "in_progress",
                "name": "В работе",
                "status": "in_progress", 
                "color": "yellow",
                "order": 2,
                "wip_limit": 3,
                "tasks": []
            },
            {
                "id": "review",
                "name": "На проверке",
                "status": "review",
                "color": "purple", 
                "order": 3,
                "wip_limit": 2,
                "tasks": []
            },
            {
                "id": "testing",
                "name": "Тестирование",
                "status": "testing",
                "color": "orange",
                "order": 4, 
                "wip_limit": 2,
                "tasks": []
            },
            {
                "id": "done",
                "name": "Выполнено",
                "status": "done",
                "color": "green",
                "order": 5,
                "wip_limit": None,
                "tasks": []
            }
        ]
        
        # Get tasks based on filters
        filters = TaskFilters(
            project_id=project_id,
            sprint_id=sprint_id
        )
        
        tasks = await project_service.get_tasks(db=db, filters=filters)
        
        # Group tasks by status
        tasks_by_status = {}
        for task in tasks:
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            if status not in tasks_by_status:
                tasks_by_status[status] = []
            
            # Convert task to dict with additional fields
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "type": task.type.value if hasattr(task.type, 'value') else str(task.type),
                "status": status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                "assignee_id": task.assignee_id,
                "assignee_name": task.assignee.username if task.assignee else None,
                "reporter_id": task.reporter_id,
                "reporter_name": task.reporter.username if task.reporter else None,
                "project_id": task.project_id,
                "project_name": task.project.name if task.project else None,
                "milestone_id": task.milestone_id,
                "sprint_id": task.sprint_id,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "story_points": task.story_points,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "completed_date": task.completed_date.isoformat() if task.completed_date else None,
                "labels": task.labels or [],
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "comments_count": len(task.comments) if hasattr(task, 'comments') else 0,
                "attachments_count": len(task.attachments) if hasattr(task, 'attachments') else 0
            }
            tasks_by_status[status].append(task_dict)
        
        # Assign tasks to columns
        for column in default_columns:
            column_status = column["status"]
            column["tasks"] = tasks_by_status.get(column_status, [])
        
        return {
            "columns": default_columns,
            "project_id": project_id,
            "sprint_id": sprint_id,
            "total_tasks": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Error getting kanban board: {e}")
        raise HTTPException(status_code=500, detail="Failed to get kanban board")


# Sprint Management Endpoints
@router.get("/sprints", response_model=List[SprintResponse])
async def get_sprints(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    status: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of sprints with optional filtering"""
    try:
        # This would be implemented in the service
        # For now, return mock data
        mock_sprints = [
            {
                "id": 1,
                "name": "Спринт 1 - Основные функции",
                "goal": "Реализация базового функционала админ-панели",
                "project_id": project_id,
                "project_name": "АДВАКОД",
                "status": "active",
                "start_date": "2025-10-20T00:00:00Z",
                "end_date": "2025-11-03T00:00:00Z", 
                "capacity": 40,
                "commitment": 35,
                "completed": 28,
                "velocity": 32.5,
                "burndown_data": None,
                "created_at": "2025-10-20T00:00:00Z",
                "updated_at": "2025-10-25T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Спринт 2 - Аналитика",
                "goal": "Добавление аналитических инструментов",
                "project_id": project_id,
                "project_name": "АДВАКОД", 
                "status": "planning",
                "start_date": "2025-11-04T00:00:00Z",
                "end_date": "2025-11-18T00:00:00Z",
                "capacity": 40,
                "commitment": 0,
                "completed": 0,
                "velocity": 32.5,
                "burndown_data": None,
                "created_at": "2025-10-25T00:00:00Z",
                "updated_at": "2025-10-25T00:00:00Z"
            }
        ]
        
        # Filter by project if specified
        if project_id:
            mock_sprints = [s for s in mock_sprints if s["project_id"] == project_id]
        
        # Filter by status if specified
        if status:
            mock_sprints = [s for s in mock_sprints if s["status"] in status]
        
        return mock_sprints[skip:skip+limit]
        
    except Exception as e:
        logger.error(f"Error getting sprints: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sprints")


@router.post("/sprints", response_model=SprintResponse)
async def create_sprint(
    sprint_data: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new sprint"""
    try:
        # This would be implemented in the service
        # For now, return mock response
        from datetime import datetime
        
        mock_sprint = {
            "id": 999,
            "name": sprint_data.name,
            "goal": sprint_data.goal,
            "project_id": sprint_data.project_id,
            "project_name": "АДВАКОД",
            "status": "planning",
            "start_date": sprint_data.start_date.isoformat(),
            "end_date": sprint_data.end_date.isoformat(),
            "capacity": sprint_data.capacity,
            "commitment": 0,
            "completed": 0,
            "velocity": 0.0,
            "burndown_data": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return mock_sprint
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating sprint: {e}")
        raise HTTPException(status_code=500, detail="Failed to create sprint")


@router.put("/sprints/{sprint_id}", response_model=SprintResponse)
async def update_sprint(
    sprint_id: int,
    sprint_data: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing sprint"""
    try:
        # This would be implemented in the service
        # For now, return mock response
        from datetime import datetime
        
        mock_sprint = {
            "id": sprint_id,
            "name": sprint_data.name or "Updated Sprint",
            "goal": sprint_data.goal,
            "project_id": 1,
            "project_name": "АДВАКОД",
            "status": sprint_data.status.value if sprint_data.status else "planning",
            "start_date": sprint_data.start_date.isoformat() if sprint_data.start_date else "2025-10-25T00:00:00Z",
            "end_date": sprint_data.end_date.isoformat() if sprint_data.end_date else "2025-11-08T00:00:00Z",
            "capacity": sprint_data.capacity or 40,
            "commitment": sprint_data.commitment or 0,
            "completed": sprint_data.completed or 0,
            "velocity": sprint_data.velocity or 0.0,
            "burndown_data": None,
            "created_at": "2025-10-25T00:00:00Z",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return mock_sprint
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating sprint {sprint_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update sprint")


# Time Tracking Endpoints
@router.get("/time-entries", response_model=List[TimeEntryResponse])
async def get_time_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    period: str = Query("week", pattern="^(today|week|month|year)$"),
    project_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    billable: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of time entries with optional filtering"""
    try:
        # This would be implemented in the service
        # For now, return mock data
        from datetime import datetime, timedelta
        
        mock_entries = [
            {
                "id": 1,
                "user_id": current_user.id,
                "user_name": current_user.username,
                "task_id": 1,
                "task_title": "Реализация A/B тестирования",
                "project_id": 1,
                "project_name": "АДВАКОД",
                "description": "Работа над компонентом ABTestManager",
                "hours": 4.5,
                "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "billable": True,
                "hourly_rate": 2500.0,
                "currency": "RUB",
                "status": "approved",
                "approved_by": None,
                "approved_at": None,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            {
                "id": 2,
                "user_id": current_user.id,
                "user_name": current_user.username,
                "task_id": 2,
                "task_title": "Создание дашборда проекта",
                "project_id": 1,
                "project_name": "АДВАКОД",
                "description": "Разработка ProjectDashboard компонента",
                "hours": 6.0,
                "date": datetime.utcnow().isoformat(),
                "billable": True,
                "hourly_rate": 2500.0,
                "currency": "RUB",
                "status": "submitted",
                "approved_by": None,
                "approved_at": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Apply filters
        if project_id:
            mock_entries = [e for e in mock_entries if e["project_id"] == project_id]
        
        if user_id:
            mock_entries = [e for e in mock_entries if e["user_id"] == user_id]
        
        if billable is not None:
            mock_entries = [e for e in mock_entries if e["billable"] == billable]
        
        return mock_entries[skip:skip+limit]
        
    except Exception as e:
        logger.error(f"Error getting time entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get time entries")


@router.post("/time-entries", response_model=TimeEntryResponse)
async def create_time_entry(
    entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new time entry"""
    try:
        # This would be implemented in the service
        # For now, return mock response
        from datetime import datetime
        
        mock_entry = {
            "id": 999,
            "user_id": current_user.id,
            "user_name": current_user.username,
            "task_id": entry_data.task_id,
            "task_title": "Новая задача",
            "project_id": entry_data.project_id,
            "project_name": "АДВАКОД",
            "description": entry_data.description,
            "hours": entry_data.hours,
            "date": entry_data.date.isoformat(),
            "billable": entry_data.billable,
            "hourly_rate": entry_data.hourly_rate,
            "currency": entry_data.currency,
            "status": "draft",
            "approved_by": None,
            "approved_at": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return mock_entry
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating time entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to create time entry")