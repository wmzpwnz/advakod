"""Add chat_mode to chat_sessions

Revision ID: 20251118_183100
Revises: 20251026_141000
Create Date: 2025-11-18 18:31:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251118_183100'
down_revision = '20251026_141000'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем поле chat_mode в таблицу chat_sessions
    op.add_column('chat_sessions', 
        sa.Column('chat_mode', sa.String(length=20), nullable=False, server_default='basic')
    )
    # Создаем индекс для быстрого поиска по режиму (опционально)
    op.create_index('ix_chat_sessions_chat_mode', 'chat_sessions', ['chat_mode'], unique=False)


def downgrade():
    # Удаляем индекс
    op.drop_index('ix_chat_sessions_chat_mode', table_name='chat_sessions')
    # Удаляем поле chat_mode
    op.drop_column('chat_sessions', 'chat_mode')

