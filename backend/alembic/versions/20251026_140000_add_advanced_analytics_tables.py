"""Add advanced analytics tables

Revision ID: 20251026_140000
Revises: 20251025_130000
Create Date: 2024-10-26 14:00:00.000000

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
    # Create dashboards table
    op.create_table('dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('layout', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboards_id'), 'dashboards', ['id'], unique=False)

    # Create dashboard_widgets table
    op.create_table('dashboard_widgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('widget_type', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('position', sa.JSON(), nullable=True),
        sa.Column('data_source', sa.String(length=255), nullable=True),
        sa.Column('refresh_interval', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_widgets_id'), 'dashboard_widgets', ['id'], unique=False)

    # Create custom_metrics table
    op.create_table('custom_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('formula', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('format_type', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_metrics_id'), 'custom_metrics', ['id'], unique=False)

    # Create metric_alerts table
    op.create_table('metric_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['metric_id'], ['custom_metrics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metric_alerts_id'), 'metric_alerts', ['id'], unique=False)

    # Create cohort_analysis table
    op.create_table('cohort_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('cohort_type', sa.String(length=50), nullable=False),
        sa.Column('period_type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cohort_analysis_id'), 'cohort_analysis', ['id'], unique=False)

    # Create user_segments table
    op.create_table('user_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False),
        sa.Column('user_count', sa.Integer(), nullable=True),
        sa.Column('is_dynamic', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_segments_id'), 'user_segments', ['id'], unique=False)

    # Create ml_predictions table
    op.create_table('ml_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('prediction_type', sa.String(length=100), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('prediction_value', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_predictions_id'), 'ml_predictions', ['id'], unique=False)

    # Create report_templates table
    op.create_table('report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=100), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('schedule', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_templates_id'), 'report_templates', ['id'], unique=False)

    # Create report_executions table
    op.create_table('report_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_executions_id'), 'report_executions', ['id'], unique=False)

    # Add relationship to users table if not exists
    try:
        op.add_column('users', sa.Column('dashboards_relation', sa.String(length=1), nullable=True))
        op.drop_column('users', 'dashboards_relation')
    except:
        pass


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_report_executions_id'), table_name='report_executions')
    op.drop_table('report_executions')
    
    op.drop_index(op.f('ix_report_templates_id'), table_name='report_templates')
    op.drop_table('report_templates')
    
    op.drop_index(op.f('ix_ml_predictions_id'), table_name='ml_predictions')
    op.drop_table('ml_predictions')
    
    op.drop_index(op.f('ix_user_segments_id'), table_name='user_segments')
    op.drop_table('user_segments')
    
    op.drop_index(op.f('ix_cohort_analysis_id'), table_name='cohort_analysis')
    op.drop_table('cohort_analysis')
    
    op.drop_index(op.f('ix_metric_alerts_id'), table_name='metric_alerts')
    op.drop_table('metric_alerts')
    
    op.drop_index(op.f('ix_custom_metrics_id'), table_name='custom_metrics')
    op.drop_table('custom_metrics')
    
    op.drop_index(op.f('ix_dashboard_widgets_id'), table_name='dashboard_widgets')
    op.drop_table('dashboard_widgets')
    
    op.drop_index(op.f('ix_dashboards_id'), table_name='dashboards')
    op.drop_table('dashboards')