"""Add backup system tables

Revision ID: 20251026_141000
Revises: 20251025_130000
Create Date: 2025-10-26 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251026_141000'
down_revision = '20251025_130000'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем таблицу записей резервного копирования
    op.create_table('backup_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('backup_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('backup_path', sa.String(length=500), nullable=True),
        sa.Column('total_size', sa.Integer(), nullable=True),
        sa.Column('components', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('compression_enabled', sa.Boolean(), nullable=True),
        sa.Column('encryption_enabled', sa.Boolean(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('files_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_records_id'), 'backup_records', ['id'], unique=False)
    op.create_index(op.f('ix_backup_records_name'), 'backup_records', ['name'], unique=False)

    # Создаем таблицу расписаний резервного копирования
    op.create_table('backup_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('backup_components', sa.JSON(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('compression_enabled', sa.Boolean(), nullable=True),
        sa.Column('encryption_enabled', sa.Boolean(), nullable=True),
        sa.Column('notify_on_success', sa.Boolean(), nullable=True),
        sa.Column('notify_on_failure', sa.Boolean(), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('notification_recipients', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_status', sa.String(length=50), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('total_runs', sa.Integer(), nullable=True),
        sa.Column('successful_runs', sa.Integer(), nullable=True),
        sa.Column('failed_runs', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_schedules_id'), 'backup_schedules', ['id'], unique=False)

    # Создаем таблицу записей восстановления
    op.create_table('restore_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_record_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('components_to_restore', sa.JSON(), nullable=False),
        sa.Column('restore_options', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('restored_components', sa.JSON(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('files_restored', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restore_records_id'), 'restore_records', ['id'], unique=False)
    op.create_index(op.f('ix_restore_records_backup_record_id'), 'restore_records', ['backup_record_id'], unique=False)

    # Создаем таблицу проверок целостности
    op.create_table('backup_integrity_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_record_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('check_type', sa.String(length=100), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('check_duration_seconds', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('files_checked', sa.Integer(), nullable=True),
        sa.Column('size_verified', sa.Integer(), nullable=True),
        sa.Column('checksum_verified', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_integrity_checks_id'), 'backup_integrity_checks', ['id'], unique=False)
    op.create_index(op.f('ix_backup_integrity_checks_backup_record_id'), 'backup_integrity_checks', ['backup_record_id'], unique=False)


def downgrade():
    # Удаляем таблицы в обратном порядке
    op.drop_index(op.f('ix_backup_integrity_checks_backup_record_id'), table_name='backup_integrity_checks')
    op.drop_index(op.f('ix_backup_integrity_checks_id'), table_name='backup_integrity_checks')
    op.drop_table('backup_integrity_checks')
    
    op.drop_index(op.f('ix_restore_records_backup_record_id'), table_name='restore_records')
    op.drop_index(op.f('ix_restore_records_id'), table_name='restore_records')
    op.drop_table('restore_records')
    
    op.drop_index(op.f('ix_backup_schedules_id'), table_name='backup_schedules')
    op.drop_table('backup_schedules')
    
    op.drop_index(op.f('ix_backup_records_name'), table_name='backup_records')
    op.drop_index(op.f('ix_backup_records_id'), table_name='backup_records')
    op.drop_table('backup_records')