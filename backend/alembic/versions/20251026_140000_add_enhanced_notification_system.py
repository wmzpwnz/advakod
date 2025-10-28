"""Add enhanced notification system

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
    notification_type_enum = postgresql.ENUM(
        'info', 'warning', 'error', 'success',
        name='notificationtype'
    )
    notification_type_enum.create(op.get_bind())
    
    notification_category_enum = postgresql.ENUM(
        'system', 'marketing', 'moderation', 'project', 'analytics', 'security',
        name='notificationcategory'
    )
    notification_category_enum.create(op.get_bind())
    
    notification_priority_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'critical',
        name='notificationpriority'
    )
    notification_priority_enum.create(op.get_bind())
    
    notification_status_enum = postgresql.ENUM(
        'pending', 'sent', 'delivered', 'failed', 'read', 'dismissed',
        name='notificationstatus'
    )
    notification_status_enum.create(op.get_bind())
    
    channel_type_enum = postgresql.ENUM(
        'email', 'push', 'sms', 'slack', 'telegram', 'webhook',
        name='channeltype'
    )
    channel_type_enum.create(op.get_bind())
    
    # Drop existing notifications table if it exists
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS push_subscriptions CASCADE")
    
    # Create enhanced notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('type', notification_type_enum, nullable=True),
        sa.Column('category', notification_category_enum, nullable=True),
        sa.Column('priority', notification_priority_enum, nullable=True),
        sa.Column('status', notification_status_enum, nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('action_text', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('group_key', sa.String(length=255), nullable=True),
        sa.Column('is_starred', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_category', 'notifications', ['category'], unique=False)
    op.create_index('ix_notifications_priority', 'notifications', ['priority'], unique=False)
    op.create_index('ix_notifications_status', 'notifications', ['status'], unique=False)
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_group_key', 'notifications', ['group_key'], unique=False)
    
    # Create notification templates table
    op.create_table('notification_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', notification_type_enum, nullable=False),
        sa.Column('category', notification_category_enum, nullable=False),
        sa.Column('priority', notification_priority_enum, nullable=True),
        sa.Column('title_template', sa.String(length=255), nullable=False),
        sa.Column('content_template', sa.Text(), nullable=False),
        sa.Column('subject_template', sa.String(length=255), nullable=True),
        sa.Column('trigger_event', sa.String(length=255), nullable=False),
        sa.Column('trigger_conditions', sa.JSON(), nullable=True),
        sa.Column('channels', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('throttle_minutes', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_notification_templates_id'), 'notification_templates', ['id'], unique=False)
    
    # Create notification channels table
    op.create_table('notification_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', channel_type_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=True),
        sa.Column('total_sent', sa.Integer(), nullable=True),
        sa.Column('total_failed', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_channels_id'), 'notification_channels', ['id'], unique=False)
    
    # Create notification history table
    op.create_table('notification_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=50), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('type', notification_type_enum, nullable=False),
        sa.Column('category', notification_category_enum, nullable=False),
        sa.Column('priority', notification_priority_enum, nullable=False),
        sa.Column('channel_type', channel_type_enum, nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=True),
        sa.Column('status', notification_status_enum, nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['notification_channels.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['notification_templates.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_history_id'), 'notification_history', ['id'], unique=False)
    op.create_index('ix_notification_history_status', 'notification_history', ['status'], unique=False)
    op.create_index('ix_notification_history_created_at', 'notification_history', ['created_at'], unique=False)
    
    # Create notification groups table
    op.create_table('notification_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('group_key', sa.String(length=255), nullable=False),
        sa.Column('category', notification_category_enum, nullable=False),
        sa.Column('priority', notification_priority_enum, nullable=False),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('dismissed_by', sa.Integer(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('first_notification_at', sa.DateTime(), nullable=False),
        sa.Column('last_notification_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dismissed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_key')
    )
    op.create_index(op.f('ix_notification_groups_id'), 'notification_groups', ['id'], unique=False)
    
    # Create enhanced push subscriptions table
    op.create_table('push_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('keys', sa.JSON(), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_push_subscriptions_id'), 'push_subscriptions', ['id'], unique=False)
    op.create_index('ix_push_subscriptions_user_id', 'push_subscriptions', ['user_id'], unique=False)
    
    # Create notification preferences table
    op.create_table('notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_preferences', sa.JSON(), nullable=True),
        sa.Column('channel_preferences', sa.JSON(), nullable=True),
        sa.Column('min_priority', notification_priority_enum, nullable=True),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=True),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_timezone', sa.String(length=50), nullable=True),
        sa.Column('digest_enabled', sa.Boolean(), nullable=True),
        sa.Column('digest_frequency', sa.String(length=20), nullable=True),
        sa.Column('digest_time', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index('ix_notification_preferences_id', table_name='notification_preferences')
    op.drop_table('notification_preferences')
    
    op.drop_index('ix_push_subscriptions_user_id', table_name='push_subscriptions')
    op.drop_index(op.f('ix_push_subscriptions_id'), table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
    
    op.drop_index(op.f('ix_notification_groups_id'), table_name='notification_groups')
    op.drop_table('notification_groups')
    
    op.drop_index('ix_notification_history_created_at', table_name='notification_history')
    op.drop_index('ix_notification_history_status', table_name='notification_history')
    op.drop_index(op.f('ix_notification_history_id'), table_name='notification_history')
    op.drop_table('notification_history')
    
    op.drop_index(op.f('ix_notification_channels_id'), table_name='notification_channels')
    op.drop_table('notification_channels')
    
    op.drop_index(op.f('ix_notification_templates_id'), table_name='notification_templates')
    op.drop_table('notification_templates')
    
    op.drop_index('ix_notifications_group_key', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_status', table_name='notifications')
    op.drop_index('ix_notifications_priority', table_name='notifications')
    op.drop_index('ix_notifications_category', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS channeltype")
    op.execute("DROP TYPE IF EXISTS notificationstatus")
    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationcategory")
    op.execute("DROP TYPE IF EXISTS notificationtype")