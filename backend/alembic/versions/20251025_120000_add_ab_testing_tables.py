"""Add A/B testing tables

Revision ID: 20251025_120000
Revises: 20251021_235429
Create Date: 2025-10-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251025_120000'
down_revision = '20251021_235429'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    ab_test_status_enum = postgresql.ENUM(
        'draft', 'running', 'paused', 'completed', 'cancelled',
        name='abtestatus'
    )
    ab_test_status_enum.create(op.get_bind())

    ab_test_type_enum = postgresql.ENUM(
        'page', 'feature', 'element', 'flow',
        name='abtesttype'
    )
    ab_test_type_enum.create(op.get_bind())

    primary_metric_enum = postgresql.ENUM(
        'conversion_rate', 'click_through_rate', 'bounce_rate', 
        'session_duration', 'revenue_per_user', 'retention_rate',
        name='primarymetric'
    )
    primary_metric_enum.create(op.get_bind())

    ab_test_event_type_enum = postgresql.ENUM(
        'view', 'click', 'conversion', 'custom',
        name='abtesteventtype'
    )
    ab_test_event_type_enum.create(op.get_bind())

    # Create ab_tests table
    op.create_table('ab_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        sa.Column('type', ab_test_type_enum, nullable=False),
        sa.Column('status', ab_test_status_enum, nullable=False),
        sa.Column('traffic_allocation', sa.Float(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('primary_metric', primary_metric_enum, nullable=False),
        sa.Column('secondary_metrics', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('winner_variant_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_tests_id'), 'ab_tests', ['id'], unique=False)
    op.create_index(op.f('ix_ab_tests_name'), 'ab_tests', ['name'], unique=False)

    # Create ab_test_variants table
    op.create_table('ab_test_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_control', sa.Boolean(), nullable=False),
        sa.Column('traffic_percentage', sa.Float(), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('participants_count', sa.Integer(), nullable=False),
        sa.Column('conversions_count', sa.Integer(), nullable=False),
        sa.Column('total_revenue', sa.Float(), nullable=False),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('statistical_significance', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_variants_id'), 'ab_test_variants', ['id'], unique=False)

    # Create ab_test_participants table
    op.create_table('ab_test_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('first_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted', sa.Boolean(), nullable=False),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('conversion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_duration', sa.Integer(), nullable=True),
        sa.Column('page_views', sa.Integer(), nullable=False),
        sa.Column('bounce', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['variant_id'], ['ab_test_variants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_participants_id'), 'ab_test_participants', ['id'], unique=False)

    # Create ab_test_events table
    op.create_table('ab_test_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('participant_id', sa.Integer(), nullable=False),
        sa.Column('event_type', ab_test_event_type_enum, nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('event_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['participant_id'], ['ab_test_participants.id'], ),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.ForeignKeyConstraint(['variant_id'], ['ab_test_variants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_events_id'), 'ab_test_events', ['id'], unique=False)

    # Create ab_test_statistics table
    op.create_table('ab_test_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('power', sa.Float(), nullable=True),
        sa.Column('effect_size', sa.Float(), nullable=True),
        sa.Column('bayesian_probability', sa.Float(), nullable=True),
        sa.Column('credible_interval_lower', sa.Float(), nullable=True),
        sa.Column('credible_interval_upper', sa.Float(), nullable=True),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('t_statistic', sa.Float(), nullable=True),
        sa.Column('degrees_of_freedom', sa.Integer(), nullable=True),
        sa.Column('winner_variant_id', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('is_significant', sa.Boolean(), nullable=False),
        sa.Column('uplift_percentage', sa.Float(), nullable=True),
        sa.Column('analysis_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['test_id'], ['ab_tests.id'], ),
        sa.ForeignKeyConstraint(['winner_variant_id'], ['ab_test_variants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_statistics_id'), 'ab_test_statistics', ['id'], unique=False)

    # Add foreign key constraint for winner_variant_id in ab_tests table
    op.create_foreign_key(None, 'ab_tests', 'ab_test_variants', ['winner_variant_id'], ['id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('ab_test_statistics')
    op.drop_table('ab_test_events')
    op.drop_table('ab_test_participants')
    op.drop_table('ab_test_variants')
    op.drop_table('ab_tests')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS abtesteventtype')
    op.execute('DROP TYPE IF EXISTS primarymetric')
    op.execute('DROP TYPE IF EXISTS abtesttype')
    op.execute('DROP TYPE IF EXISTS abtestatus')