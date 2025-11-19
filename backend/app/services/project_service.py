import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
import logging

from ..models.project import (
    Project, ProjectMember, Task, TaskComment, TaskAttachment, TaskDependency,
    Milestone, Sprint, TimeEntry, ResourceAllocation, ProjectAllocation, AvailabilityPeriod,
    ProjectStatus, TaskStatus, MilestoneStatus, SprintStatus
)
from ..models.user import User
from ..schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectFilters,
    TaskCreate, TaskUpdate, TaskFilters,
    MilestoneCreate, MilestoneUpdate,
    SprintCreate, SprintUpdate,
    TimeEntryCreate, TimeEntryUpdate,
    ProjectDashboardResponse, ProjectDashboardStats,
    VelocityPoint, ResourceUtilization, ProjectActivity, UpcomingDeadline
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects, tasks, and resources"""

    def __init__(self):
        self.logger = logger

    # Project Management
    async def create_project(self, db: Session, project_data: ProjectCreate, creator_id: int) -> Project:
        """Create a new project with initial members"""
        try:
            # Create the project
            project = Project(
                name=project_data.name,
                description=project_data.description,
                key=project_data.key,
                type=project_data.type,
                visibility=project_data.visibility,
                lead_id=project_data.lead_id,
                start_date=project_data.start_date,
                end_date=project_data.end_date,
                budget=project_data.budget,
                currency=project_data.currency
            )
            
            db.add(project)
            db.flush()  # Get the project ID
            
            # Add project members
            members_to_add = project_data.members or []
            
            # Ensure project lead is a member
            lead_member_exists = any(m.user_id == project_data.lead_id for m in members_to_add)
            if not lead_member_exists:
                members_to_add.append({
                    'user_id': project_data.lead_id,
                    'role': 'owner',
                    'allocation': 100.0,
                    'is_active': True
                })
            
            for member_data in members_to_add:
                member = ProjectMember(
                    project_id=project.id,
                    user_id=member_data.user_id,
                    role=member_data.role,
                    allocation=member_data.allocation,
                    is_active=member_data.is_active
                )
                db.add(member)
            
            db.commit()
            db.refresh(project)
            
            self.logger.info(f"Created project: {project.name} (ID: {project.id})")
            return project
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Failed to create project: {e}")
            raise ValueError("Project key must be unique")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating project: {e}")
            raise

    async def get_project(self, db: Session, project_id: int) -> Optional[Project]:
        """Get a specific project with all related data"""
        return db.query(Project).filter(Project.id == project_id).first()

    async def get_projects(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[ProjectFilters] = None,
        user_id: Optional[int] = None
    ) -> List[Project]:
        """Get list of projects with optional filtering"""
        query = db.query(Project)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(Project.status.in_(filters.status))
            if filters.type:
                query = query.filter(Project.type.in_(filters.type))
            if filters.health:
                query = query.filter(Project.health.in_(filters.health))
            if filters.lead_id:
                query = query.filter(Project.lead_id == filters.lead_id)
            if filters.member_id:
                query = query.join(ProjectMember).filter(
                    and_(
                        ProjectMember.user_id == filters.member_id,
                        ProjectMember.is_active == True
                    )
                )
            if filters.date_range:
                if filters.date_range.get('start'):
                    query = query.filter(Project.start_date >= filters.date_range['start'])
                if filters.date_range.get('end'):
                    query = query.filter(Project.end_date <= filters.date_range['end'])
        
        # Filter by user access if specified
        if user_id:
            query = query.outerjoin(ProjectMember).filter(
                or_(
                    Project.lead_id == user_id,
                    and_(
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True
                    ),
                    Project.visibility == 'public'
                )
            )
        
        return query.order_by(desc(Project.updated_at)).offset(skip).limit(limit).all()

    async def update_project(self, db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """Update an existing project"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Update fields
        for field, value in project_data.dict(exclude_unset=True).items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        
        self.logger.info(f"Updated project: {project.name} (ID: {project.id})")
        return project

    async def delete_project(self, db: Session, project_id: int) -> bool:
        """Delete a project and all related data"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        
        self.logger.info(f"Deleted project: {project.name} (ID: {project.id})")
        return True

    # Task Management
    async def create_task(self, db: Session, task_data: TaskCreate) -> Task:
        """Create a new task"""
        try:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                type=task_data.type,
                priority=task_data.priority,
                assignee_id=task_data.assignee_id,
                reporter_id=task_data.reporter_id,
                project_id=task_data.project_id,
                milestone_id=task_data.milestone_id,
                sprint_id=task_data.sprint_id,
                parent_task_id=task_data.parent_task_id,
                estimated_hours=task_data.estimated_hours,
                story_points=task_data.story_points,
                due_date=task_data.due_date,
                start_date=task_data.start_date,
                labels=task_data.labels or [],
                custom_fields=task_data.custom_fields or {}
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Update project task count
            if task.project_id:
                await self._update_project_task_counts(db, task.project_id)
            
            self.logger.info(f"Created task: {task.title} (ID: {task.id})")
            return task
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating task: {e}")
            raise

    async def get_task(self, db: Session, task_id: int) -> Optional[Task]:
        """Get a specific task with all related data"""
        return db.query(Task).filter(Task.id == task_id).first()

    async def get_tasks(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[TaskFilters] = None
    ) -> List[Task]:
        """Get list of tasks with optional filtering"""
        query = db.query(Task)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(Task.status.in_(filters.status))
            if filters.type:
                query = query.filter(Task.type.in_(filters.type))
            if filters.priority:
                query = query.filter(Task.priority.in_(filters.priority))
            if filters.assignee_id:
                query = query.filter(Task.assignee_id == filters.assignee_id)
            if filters.reporter_id:
                query = query.filter(Task.reporter_id == filters.reporter_id)
            if filters.project_id:
                query = query.filter(Task.project_id == filters.project_id)
            if filters.milestone_id:
                query = query.filter(Task.milestone_id == filters.milestone_id)
            if filters.sprint_id:
                query = query.filter(Task.sprint_id == filters.sprint_id)
            if filters.labels:
                # Filter tasks that have any of the specified labels
                for label in filters.labels:
                    query = query.filter(Task.labels.contains([label]))
            if filters.date_range:
                if filters.date_range.get('start'):
                    query = query.filter(Task.created_at >= filters.date_range['start'])
                if filters.date_range.get('end'):
                    query = query.filter(Task.created_at <= filters.date_range['end'])
        
        return query.order_by(desc(Task.updated_at)).offset(skip).limit(limit).all()

    async def update_task(self, db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        old_status = task.status
        
        # Update fields
        for field, value in task_data.dict(exclude_unset=True).items():
            setattr(task, field, value)
        
        # Set completion date if task is marked as done
        if task_data.status == TaskStatus.DONE and old_status != TaskStatus.DONE:
            task.completed_date = datetime.utcnow()
        elif task_data.status != TaskStatus.DONE and old_status == TaskStatus.DONE:
            task.completed_date = None
        
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        
        # Update project task counts if status changed
        if task.project_id and old_status != task.status:
            await self._update_project_task_counts(db, task.project_id)
        
        self.logger.info(f"Updated task: {task.title} (ID: {task.id})")
        return task

    async def delete_task(self, db: Session, task_id: int) -> bool:
        """Delete a task"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        project_id = task.project_id
        
        db.delete(task)
        db.commit()
        
        # Update project task counts
        if project_id:
            await self._update_project_task_counts(db, project_id)
        
        self.logger.info(f"Deleted task: {task.title} (ID: {task.id})")
        return True

    # Dashboard and Analytics
    async def get_dashboard_data(self, db: Session, period: str = "30d") -> ProjectDashboardResponse:
        """Get comprehensive dashboard data"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:  # 30d default
                start_date = end_date - timedelta(days=30)
            
            # Basic project statistics
            total_projects = db.query(Project).count()
            active_projects = db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).count()
            completed_projects = db.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count()
            
            # Overdue tasks
            overdue_tasks = db.query(Task).filter(
                and_(
                    Task.due_date < datetime.utcnow(),
                    Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED])
                )
            ).count()
            
            # Team members count
            total_team_members = db.query(ProjectMember).filter(
                ProjectMember.is_active == True
            ).distinct(ProjectMember.user_id).count()
            
            # Average project health (simplified calculation)
            health_scores = {'green': 3, 'yellow': 2, 'red': 1}
            avg_health_query = db.query(func.avg(
                func.case(
                    (Project.health == 'green', 3),
                    (Project.health == 'yellow', 2),
                    (Project.health == 'red', 1),
                    else_=2
                )
            )).filter(Project.status == ProjectStatus.ACTIVE).scalar()
            
            average_project_health = (avg_health_query or 2) / 3 * 100
            
            # Budget utilization (simplified)
            budget_query = db.query(
                func.sum(Project.budget),
                func.sum(Project.spent_budget)
            ).filter(
                and_(
                    Project.status == ProjectStatus.ACTIVE,
                    Project.budget.isnot(None)
                )
            ).first()
            
            total_budget = budget_query[0] or 0
            spent_budget = budget_query[1] or 0
            budget_utilization = (spent_budget / total_budget * 100) if total_budget > 0 else 0
            
            stats = ProjectDashboardStats(
                total_projects=total_projects,
                active_projects=active_projects,
                completed_projects=completed_projects,
                overdue_tasks=overdue_tasks,
                total_team_members=total_team_members,
                average_project_health=average_project_health,
                budget_utilization=budget_utilization
            )
            
            # Velocity trend (last 5 sprints)
            velocity_trend = await self._get_velocity_trend(db, limit=5)
            
            # Resource utilization
            resource_utilization = await self._get_resource_utilization(db)
            
            # Upcoming deadlines
            upcoming_deadlines = await self._get_upcoming_deadlines(db, limit=10)
            
            # Recent activity
            recent_activity = await self._get_recent_activity(db, start_date, limit=20)
            
            return ProjectDashboardResponse(
                stats=stats,
                velocity_trend=velocity_trend,
                resource_utilization=resource_utilization,
                upcoming_deadlines=upcoming_deadlines,
                recent_activity=recent_activity,
                period=period,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            raise

    # Private helper methods
    async def _update_project_task_counts(self, db: Session, project_id: int):
        """Update task counts for a project"""
        total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
        completed_tasks = db.query(Task).filter(
            and_(
                Task.project_id == project_id,
                Task.status == TaskStatus.DONE
            )
        ).count()
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.total_tasks = total_tasks
            project.completed_tasks = completed_tasks
            project.progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            db.commit()

    async def _get_velocity_trend(self, db: Session, limit: int = 5) -> List[VelocityPoint]:
        """Get velocity trend data from recent sprints"""
        sprints = db.query(Sprint).filter(
            Sprint.status == SprintStatus.COMPLETED
        ).order_by(desc(Sprint.end_date)).limit(limit).all()
        
        velocity_points = []
        for sprint in sprints:
            velocity_points.append(VelocityPoint(
                sprint_name=sprint.name,
                planned=sprint.commitment,
                completed=sprint.completed,
                date=sprint.end_date
            ))
        
        return list(reversed(velocity_points))  # Chronological order

    async def _get_resource_utilization(self, db: Session) -> List[ResourceUtilization]:
        """Get current resource utilization data"""
        # This is a simplified implementation
        # In a real system, you'd calculate based on actual allocations and time entries
        
        active_members = db.query(ProjectMember).filter(
            ProjectMember.is_active == True
        ).all()
        
        utilization_data = []
        for member in active_members:
            # Simplified calculation - in reality, you'd sum up all project allocations
            utilization_data.append(ResourceUtilization(
                user_id=member.user_id,
                user_name=member.user.username if member.user else "Unknown",
                total_capacity=40.0,  # 40 hours per week
                allocated=member.allocation / 100 * 40,
                utilization=member.allocation,
                overallocated=member.allocation > 100
            ))
        
        return utilization_data

    async def _get_upcoming_deadlines(self, db: Session, limit: int = 10) -> List[UpcomingDeadline]:
        """Get upcoming deadlines from milestones and tasks"""
        deadlines = []
        
        # Upcoming milestones
        milestones = db.query(Milestone).filter(
            and_(
                Milestone.due_date > datetime.utcnow(),
                Milestone.status.in_([MilestoneStatus.PLANNING, MilestoneStatus.ACTIVE])
            )
        ).order_by(asc(Milestone.due_date)).limit(limit).all()
        
        for milestone in milestones:
            deadlines.append(UpcomingDeadline(
                id=milestone.id,
                name=milestone.name,
                type="milestone",
                due_date=milestone.due_date,
                progress=milestone.progress,
                project_id=milestone.project_id,
                project_name=milestone.project.name if milestone.project else None
            ))
        
        # Upcoming task deadlines
        tasks = db.query(Task).filter(
            and_(
                Task.due_date > datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED])
            )
        ).order_by(asc(Task.due_date)).limit(limit).all()
        
        for task in tasks:
            deadlines.append(UpcomingDeadline(
                id=task.id,
                name=task.title,
                type="task",
                due_date=task.due_date,
                progress=100.0 if task.status == TaskStatus.DONE else 0.0,
                project_id=task.project_id,
                project_name=task.project.name if task.project else None,
                priority=task.priority.value
            ))
        
        # Sort by due date and limit
        deadlines.sort(key=lambda x: x.due_date)
        return deadlines[:limit]

    async def _get_recent_activity(self, db: Session, start_date: datetime, limit: int = 20) -> List[ProjectActivity]:
        """Get recent project activity"""
        activities = []
        
        # Recent task updates
        recent_tasks = db.query(Task).filter(
            Task.updated_at >= start_date
        ).order_by(desc(Task.updated_at)).limit(limit).all()
        
        for task in recent_tasks:
            if task.status == TaskStatus.DONE:
                activity_type = "task_completed"
                description = f"завершил задачу '{task.title}'"
            else:
                activity_type = "task_updated"
                description = f"обновил задачу '{task.title}'"
            
            activities.append(ProjectActivity(
                id=task.id,
                type=activity_type,
                description=description,
                user_id=task.assignee_id or task.reporter_id,
                user_name=task.assignee.username if task.assignee else (task.reporter.username if task.reporter else "Unknown"),
                project_id=task.project_id,
                project_name=task.project.name if task.project else None,
                task_id=task.id,
                task_title=task.title,
                created_at=task.updated_at
            ))
        
        # Sort by date and limit
        activities.sort(key=lambda x: x.created_at, reverse=True)
        return activities[:limit]


# Global service instance
project_service = ProjectService()