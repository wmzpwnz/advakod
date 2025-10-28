"""Add monitoring integration tables

Revision ID: 20251026_140000
Revises: 20251025_130000
Create Date: 2025-10-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251026_140000'
down_revision = '20251025_130000'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    incident_status_enum = sa.Enum(
        'OPEN', 'INVESTIGATING', 'IDENTIFIED', 'MONITORING', 'RESOLVED', 'CLOSED',
        name='incidentstatus'
    )
    incident_severity_enum = sa.Enum(
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
        name='incidentseverity'
    )
    alert_status_enum = sa.Enum(
        'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', 'SUPPRESSED',
        name='alertstatus'
    )
    
    incident_status_enum.create(op.get_bind())
    incident_severity_enum.create(op.get_bind())
    alert_status_enum.create(op.get_bind())
    
    # Create incidents table
    op.create_table('incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', incident_severity_enum, nullable=False),
        sa.Column('status', incident_status_enum, nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('alert_rule', sa.String(length=255), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('related_task_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('affected_services', sa.JSON(), nullable=True),
        sa.Column('affected_users_count', sa.Integer(), nullable=False),
        sa.Column('downtime_minutes', sa.Float(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_title'), 'incidents', ['title'], unique=False)
    
    # Create monitoring_alerts table
    op.create_table('monitoring_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', incident_severity_enum, nullable=False),
        sa.Column('status', alert_status_enum, nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('auto_task_created', sa.Boolean(), nullable=False),
        sa.Column('created_task_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('annotations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_alerts_id'), 'monitoring_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_monitoring_alerts_name'), 'monitoring_alerts', ['name'], unique=False)
    
    # Create incident_updates table
    op.create_table('incident_updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('update_type', sa.String(length=50), nullable=False),
        sa.Column('old_status', incident_status_enum, nullable=True),
        sa.Column('new_status', incident_status_enum, nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incident_updates_id'), 'incident_updates', ['id'], unique=False)
    
    # Create operational_metrics table
    op.create_table('operational_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('warning_threshold', sa.Float(), nullable=True),
        sa.Column('critical_threshold', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operational_metrics_id'), 'operational_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_operational_metrics_name'), 'operational_metrics', ['name'], unique=False)
    
    # Create metric_values table
    op.create_table('metric_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['metric_id'], ['operational_metrics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metric_values_id'), 'metric_values', ['id'], unique=False)
    
    # Set default values for new columns
    op.execute("UPDATE incidents SET affected_users_count = 0 WHERE affected_users_count IS NULL")
    op.execute("UPDATE incidents SET downtime_minutes = 0.0 WHERE downtime_minutes IS NULL")
    op.execute("UPDATE monitoring_alerts SET auto_task_created = false WHERE auto_task_created IS NULL")
    op.execute("UPDATE incident_updates SET is_public = true WHERE is_public IS NULL")
    op.execute("UPDATE operational_metrics SET order_index = 0 WHERE order_index IS NULL")
    op.execute("UPDATE operational_metrics SET is_active = true WHERE is_active IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_metric_values_id'), table_name='metric_values')
    op.drop_table('metric_values')
    
    op.drop_index(op.f('ix_operational_metrics_name'), table_name='operational_metrics')
    op.drop_index(op.f('ix_operational_metrics_id'), table_name='operational_metrics')
    op.drop_table('operational_metrics')
    
    op.drop_index(op.f('ix_incident_updates_id'), table_name='incident_updates')
    op.drop_table('incident_updates')
    
    op.drop_index(op.f('ix_monitoring_alerts_name'), table_name='monitoring_alerts')
    op.drop_index(op.f('ix_monitoring_alerts_id'), table_name='monitoring_alerts')
    op.drop_table('monitoring_alerts')
    
    op.drop_index(op.f('ix_incidents_title'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_id'), table_name='incidents')
    op.drop_table('incidents')
    
    # Drop enum types
    sa.Enum(name='alertstatus').drop(op.get_bind())
    sa.Enum(name='incidentseverity').drop(op.get_bind())
    sa.Enum(name='incidentstatus').drop(op.get_bind())