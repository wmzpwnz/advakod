"""Add project management tables

Revision ID: 20251025_130000
Revises: 20251025_120000
Create Date: 2025-10-25 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251025_130000'
down_revision = '20251025_120000'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    project_status_enum = postgresql.ENUM(
        'planning', 'active', 'on_hold', 'completed', 'cancelled',
        name='projectstatus'
    )
    project_status_enum.create(op.get_bind())

    project_type_enum = postgresql.ENUM(
        'software', 'marketing', 'research', 'operations',
        name='projecttype'
    )
    project_type_enum.create(op.get_bind())

    project_visibility_enum = postgresql.ENUM(
        'public', 'private', 'team',
        name='projectvisibility'
    )
    project_visibility_enum.create(op.get_bind())

    project_health_enum = postgresql.ENUM(
        'green', 'yellow', 'red',
        name='projecthealth'
    )
    project_health_enum.create(op.get_bind())

    task_status_enum = postgresql.ENUM(
        'backlog', 'todo', 'in_progress', 'review', 'testing', 'done', 'cancelled',
        name='taskstatus'
    )
    task_status_enum.create(op.get_bind())

    task_type_enum = postgresql.ENUM(
        'feature', 'bug', 'improvement', 'maintenance', 'research', 'documentation',
        name='tasktype'
    )
    task_type_enum.create(op.get_bind())

    task_priority_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'critical',
        name='taskpriority'
    )
    task_priority_enum.create(op.get_bind())

    milestone_status_enum = postgresql.ENUM(
        'planning', 'active', 'completed', 'cancelled', 'overdue',
        name='milestonestatus'
    )
    milestone_status_enum.create(op.get_bind())

    sprint_status_enum = postgresql.ENUM(
        'planning', 'active', 'completed', 'cancelled',
        name='sprintstatus'
    )
    sprint_status_enum.create(op.get_bind())

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('key', sa.String(length=10), nullable=False),
        sa.Column('type', project_type_enum, nullable=False),
        sa.Column('status', project_status_enum, nullable=False),
        sa.Column('visibility', project_visibility_enum, nullable=False),
        sa.Column('health', project_health_enum, nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('spent_budget', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('total_tasks', sa.Integer(), nullable=False),
        sa.Column('completed_tasks', sa.Integer(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_key'), 'projects', ['key'], unique=False)

    # Create project_members table
    op.create_table('project_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('allocation', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_members_id'), 'project_members', ['id'], unique=False)

    # Create milestones table
    op.create_table('milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('status', milestone_status_enum, nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('total_tasks', sa.Integer(), nullable=False),
        sa.Column('completed_tasks', sa.Integer(), nullable=False),
        sa.Column('total_story_points', sa.Integer(), nullable=True),
        sa.Column('completed_story_points', sa.Integer(), nullable=False),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('spent_budget', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_id'), 'milestones', ['id'], unique=False)
    op.create_index(op.f('ix_milestones_name'), 'milestones', ['name'], unique=False)

    # Create sprints table
    op.create_table('sprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('status', sprint_status_enum, nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('commitment', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Integer(), nullable=False),
        sa.Column('velocity', sa.Float(), nullable=False),
        sa.Column('burndown_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sprints_id'), 'sprints', ['id'], unique=False)
    op.create_index(op.f('ix_sprints_name'), 'sprints', ['name'], unique=False)

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', task_type_enum, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('priority', task_priority_enum, nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('sprint_id', sa.Integer(), nullable=True),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=False),
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)

    # Create task_comments table
    op.create_table('task_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_edited', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_comments_id'), 'task_comments', ['id'], unique=False)

    # Create task_attachments table
    op.create_table('task_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_attachments_id'), 'task_attachments', ['id'], unique=False)

    # Create task_dependencies table
    op.create_table('task_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('depends_on_task_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['depends_on_task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_dependencies_id'), 'task_dependencies', ['id'], unique=False)

    # Create time_entries table
    op.create_table('time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('billable', sa.Boolean(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_entries_id'), 'time_entries', ['id'], unique=False)

    # Create resource_allocations table
    op.create_table('resource_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_capacity', sa.Float(), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_allocations_id'), 'resource_allocations', ['id'], unique=False)

    # Create project_allocations table
    op.create_table('project_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('allocation', sa.Float(), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['resource_id'], ['resource_allocations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_allocations_id'), 'project_allocations', ['id'], unique=False)

    # Create availability_periods table
    op.create_table('availability_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resource_id'], ['resource_allocations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_availability_periods_id'), 'availability_periods', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('availability_periods')
    op.drop_table('project_allocations')
    op.drop_table('resource_allocations')
    op.drop_table('time_entries')
    op.drop_table('task_dependencies')
    op.drop_table('task_attachments')
    op.drop_table('task_comments')
    op.drop_table('tasks')
    op.drop_table('sprints')
    op.drop_table('milestones')
    op.drop_table('project_members')
    op.drop_table('projects')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS sprintstatus')
    op.execute('DROP TYPE IF EXISTS milestonestatus')
    op.execute('DROP TYPE IF EXISTS taskpriority')
    op.execute('DROP TYPE IF EXISTS tasktype')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS projecthealth')
    op.execute('DROP TYPE IF EXISTS projectvisibility')
    op.execute('DROP TYPE IF EXISTS projecttype')
    op.execute('DROP TYPE IF EXISTS projectstatus')