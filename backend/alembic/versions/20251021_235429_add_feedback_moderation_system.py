"""add feedback and moderation system

Revision ID: 20251021_235429
Revises: 
Create Date: 2025-10-21 23:54:29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251021_235429'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create problem_categories table
    op.create_table(
        'problem_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_problem_categories_id'), 'problem_categories', ['id'], unique=False)
    op.create_index(op.f('ix_problem_categories_name'), 'problem_categories', ['name'], unique=True)
    op.create_index(op.f('ix_problem_categories_is_active'), 'problem_categories', ['is_active'], unique=False)

    # Create response_feedback table
    op.create_table(
        'response_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('feedback_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_response_feedback_id'), 'response_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_response_feedback_message_id'), 'response_feedback', ['message_id'], unique=False)
    op.create_index(op.f('ix_response_feedback_user_id'), 'response_feedback', ['user_id'], unique=False)
    op.create_index(op.f('ix_response_feedback_rating'), 'response_feedback', ['rating'], unique=False)
    op.create_index(op.f('ix_response_feedback_created_at'), 'response_feedback', ['created_at'], unique=False)

    # Create moderation_reviews table
    op.create_table(
        'moderation_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('moderator_id', sa.Integer(), nullable=False),
        sa.Column('star_rating', sa.Integer(), nullable=False),
        sa.Column('problem_categories', sa.JSON(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='reviewed'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('original_confidence', sa.Float(), nullable=True),
        sa.Column('review_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_reviews_id'), 'moderation_reviews', ['id'], unique=False)
    op.create_index(op.f('ix_moderation_reviews_message_id'), 'moderation_reviews', ['message_id'], unique=False)
    op.create_index(op.f('ix_moderation_reviews_moderator_id'), 'moderation_reviews', ['moderator_id'], unique=False)
    op.create_index(op.f('ix_moderation_reviews_status'), 'moderation_reviews', ['status'], unique=False)
    op.create_index(op.f('ix_moderation_reviews_priority'), 'moderation_reviews', ['priority'], unique=False)
    op.create_index(op.f('ix_moderation_reviews_created_at'), 'moderation_reviews', ['created_at'], unique=False)

    # Create training_datasets table
    op.create_table(
        'training_datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('bad_answer', sa.Text(), nullable=False),
        sa.Column('good_answer', sa.Text(), nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=True),
        sa.Column('dataset_metadata', sa.JSON(), nullable=True),
        sa.Column('used_in_training', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['review_id'], ['moderation_reviews.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_datasets_id'), 'training_datasets', ['id'], unique=False)
    op.create_index(op.f('ix_training_datasets_version'), 'training_datasets', ['version'], unique=False)
    op.create_index(op.f('ix_training_datasets_used_in_training'), 'training_datasets', ['used_in_training'], unique=False)
    op.create_index(op.f('ix_training_datasets_created_at'), 'training_datasets', ['created_at'], unique=False)

    # Create moderator_stats table
    op.create_table(
        'moderator_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moderator_id', sa.Integer(), nullable=False),
        sa.Column('total_reviews', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('points', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('badges', sa.JSON(), nullable=True),
        sa.Column('rank', sa.String(length=20), nullable=True, server_default='novice'),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('category_stats', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('moderator_id')
    )
    op.create_index(op.f('ix_moderator_stats_id'), 'moderator_stats', ['id'], unique=False)
    op.create_index(op.f('ix_moderator_stats_moderator_id'), 'moderator_stats', ['moderator_id'], unique=True)
    op.create_index(op.f('ix_moderator_stats_points'), 'moderator_stats', ['points'], unique=False)
    op.create_index(op.f('ix_moderator_stats_rank'), 'moderator_stats', ['rank'], unique=False)

    # Create moderation_queue table
    op.create_table(
        'moderation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('queue_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index(op.f('ix_moderation_queue_id'), 'moderation_queue', ['id'], unique=False)
    op.create_index(op.f('ix_moderation_queue_message_id'), 'moderation_queue', ['message_id'], unique=True)
    op.create_index(op.f('ix_moderation_queue_priority'), 'moderation_queue', ['priority'], unique=False)
    op.create_index(op.f('ix_moderation_queue_assigned_to'), 'moderation_queue', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_moderation_queue_status'), 'moderation_queue', ['status'], unique=False)
    op.create_index(op.f('ix_moderation_queue_created_at'), 'moderation_queue', ['created_at'], unique=False)

    # Insert default problem categories
    op.execute("""
        INSERT INTO problem_categories (name, display_name, description, severity, icon, display_order) VALUES
        ('inaccurate_info', 'Неточная информация', 'Ответ содержит фактические ошибки или неточности', 5, '❌', 1),
        ('outdated_data', 'Устаревшие данные', 'Информация устарела и не соответствует текущему законодательству', 4, '📅', 2),
        ('wrong_article', 'Неправильная статья закона', 'Указана неверная статья или номер закона', 5, '📜', 3),
        ('poor_structure', 'Плохая структура ответа', 'Ответ плохо структурирован, сложно читать', 2, '🏗️', 4),
        ('missing_sources', 'Отсутствие ссылок на источники', 'Нет ссылок на законы, статьи или судебную практику', 3, '🔗', 5),
        ('hallucination', 'Галлюцинации', 'Выдуманные факты, несуществующие законы или статьи', 5, '🌀', 6),
        ('incomplete_answer', 'Неполный ответ', 'Ответ не раскрывает вопрос полностью', 3, '📝', 7),
        ('other', 'Другое', 'Другие проблемы, не входящие в категории выше', 2, '⚠️', 8)
    """)


def downgrade():
    op.drop_index(op.f('ix_moderation_queue_created_at'), table_name='moderation_queue')
    op.drop_index(op.f('ix_moderation_queue_status'), table_name='moderation_queue')
    op.drop_index(op.f('ix_moderation_queue_assigned_to'), table_name='moderation_queue')
    op.drop_index(op.f('ix_moderation_queue_priority'), table_name='moderation_queue')
    op.drop_index(op.f('ix_moderation_queue_message_id'), table_name='moderation_queue')
    op.drop_index(op.f('ix_moderation_queue_id'), table_name='moderation_queue')
    op.drop_table('moderation_queue')
    
    op.drop_index(op.f('ix_moderator_stats_rank'), table_name='moderator_stats')
    op.drop_index(op.f('ix_moderator_stats_points'), table_name='moderator_stats')
    op.drop_index(op.f('ix_moderator_stats_moderator_id'), table_name='moderator_stats')
    op.drop_index(op.f('ix_moderator_stats_id'), table_name='moderator_stats')
    op.drop_table('moderator_stats')
    
    op.drop_index(op.f('ix_training_datasets_created_at'), table_name='training_datasets')
    op.drop_index(op.f('ix_training_datasets_used_in_training'), table_name='training_datasets')
    op.drop_index(op.f('ix_training_datasets_version'), table_name='training_datasets')
    op.drop_index(op.f('ix_training_datasets_id'), table_name='training_datasets')
    op.drop_table('training_datasets')
    
    op.drop_index(op.f('ix_moderation_reviews_created_at'), table_name='moderation_reviews')
    op.drop_index(op.f('ix_moderation_reviews_priority'), table_name='moderation_reviews')
    op.drop_index(op.f('ix_moderation_reviews_status'), table_name='moderation_reviews')
    op.drop_index(op.f('ix_moderation_reviews_moderator_id'), table_name='moderation_reviews')
    op.drop_index(op.f('ix_moderation_reviews_message_id'), table_name='moderation_reviews')
    op.drop_index(op.f('ix_moderation_reviews_id'), table_name='moderation_reviews')
    op.drop_table('moderation_reviews')
    
    op.drop_index(op.f('ix_response_feedback_created_at'), table_name='response_feedback')
    op.drop_index(op.f('ix_response_feedback_rating'), table_name='response_feedback')
    op.drop_index(op.f('ix_response_feedback_user_id'), table_name='response_feedback')
    op.drop_index(op.f('ix_response_feedback_message_id'), table_name='response_feedback')
    op.drop_index(op.f('ix_response_feedback_id'), table_name='response_feedback')
    op.drop_table('response_feedback')
    
    op.drop_index(op.f('ix_problem_categories_is_active'), table_name='problem_categories')
    op.drop_index(op.f('ix_problem_categories_name'), table_name='problem_categories')
    op.drop_index(op.f('ix_problem_categories_id'), table_name='problem_categories')
    op.drop_table('problem_categories')
