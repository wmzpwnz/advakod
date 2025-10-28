"""Add admin notifications tables

Revision ID: add_admin_notifications
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_admin_notifications'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Create admin_notifications table
    op.create_table('admin_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('channels', sa.JSON(), nullable=True),
        sa.Column('delivery_status', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_notifications_id'), 'admin_notifications', ['id'], unique=False)
    op.create_index(op.f('ix_admin_notifications_user_id'), 'admin_notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_admin_notifications_type'), 'admin_notifications', ['type'], unique=False)
    op.create_index(op.f('ix_admin_notifications_priority'), 'admin_notifications', ['priority'], unique=False)
    op.create_index(op.f('ix_admin_notifications_read'), 'admin_notifications', ['read'], unique=False)

    # Create notification_templates table
    op.create_table('notification_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title_template', sa.String(length=200), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('email_template', sa.Text(), nullable=True),
        sa.Column('slack_template', sa.Text(), nullable=True),
        sa.Column('default_channels', sa.JSON(), nullable=True),
        sa.Column('default_priority', sa.String(length=20), nullable=True),
        sa.Column('trigger_conditions', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_templates_id'), 'notification_templates', ['id'], unique=False)
    op.create_index(op.f('ix_notification_templates_name'), 'notification_templates', ['name'], unique=True)
    op.create_index(op.f('ix_notification_templates_type'), 'notification_templates', ['type'], unique=False)
    op.create_index(op.f('ix_notification_templates_active'), 'notification_templates', ['active'], unique=False)

    # Create notification_history table
    op.create_table('notification_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('delivery_details', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['admin_notifications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_history_id'), 'notification_history', ['id'], unique=False)
    op.create_index(op.f('ix_notification_history_notification_id'), 'notification_history', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_history_channel'), 'notification_history', ['channel'], unique=False)
    op.create_index(op.f('ix_notification_history_status'), 'notification_history', ['status'], unique=False)

    # Set default values
    op.execute("UPDATE admin_notifications SET priority = 'normal' WHERE priority IS NULL")
    op.execute("UPDATE admin_notifications SET read = false WHERE read IS NULL")
    op.execute("UPDATE notification_templates SET default_priority = 'normal' WHERE default_priority IS NULL")
    op.execute("UPDATE notification_templates SET active = true WHERE active IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_notification_history_status'), table_name='notification_history')
    op.drop_index(op.f('ix_notification_history_channel'), table_name='notification_history')
    op.drop_index(op.f('ix_notification_history_notification_id'), table_name='notification_history')
    op.drop_index(op.f('ix_notification_history_id'), table_name='notification_history')
    op.drop_table('notification_history')

    op.drop_index(op.f('ix_notification_templates_active'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_type'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_name'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_id'), table_name='notification_templates')
    op.drop_table('notification_templates')

    op.drop_index(op.f('ix_admin_notifications_read'), table_name='admin_notifications')
    op.drop_index(op.f('ix_admin_notifications_priority'), table_name='admin_notifications')
    op.drop_index(op.f('ix_admin_notifications_type'), table_name='admin_notifications')
    op.drop_index(op.f('ix_admin_notifications_user_id'), table_name='admin_notifications')
    op.drop_index(op.f('ix_admin_notifications_id'), table_name='admin_notifications')
    op.drop_table('admin_notifications')