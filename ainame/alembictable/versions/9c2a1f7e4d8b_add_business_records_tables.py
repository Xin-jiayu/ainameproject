"""add business records tables

Revision ID: 9c2a1f7e4d8b
Revises: 6f0a8d1c2b3e
Create Date: 2026-06-28 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c2a1f7e4d8b'
down_revision: Union[str, None] = '6f0a8d1c2b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'name_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('thread_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='success', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_name_records_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_name_records')),
        sa.UniqueConstraint('thread_id', name=op.f('uq_name_records_thread_id'))
    )
    op.create_index(op.f('ix_name_records_category'), 'name_records', ['category'], unique=False)
    op.create_index(op.f('ix_name_records_is_deleted'), 'name_records', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_name_records_status'), 'name_records', ['status'], unique=False)
    op.create_index(op.f('ix_name_records_thread_id'), 'name_records', ['thread_id'], unique=False)
    op.create_index(op.f('ix_name_records_user_id'), 'name_records', ['user_id'], unique=False)

    op.create_table(
        'knowledge_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_knowledge_files_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_knowledge_files'))
    )
    op.create_index(op.f('ix_knowledge_files_status'), 'knowledge_files', ['status'], unique=False)
    op.create_index(op.f('ix_knowledge_files_user_id'), 'knowledge_files', ['user_id'], unique=False)

    op.create_table(
        'name_feedbacks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.String(length=100), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['record_id'], ['name_records.id'], name=op.f('fk_name_feedbacks_record_id_name_records')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_name_feedbacks_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_name_feedbacks'))
    )
    op.create_index(op.f('ix_name_feedbacks_record_id'), 'name_feedbacks', ['record_id'], unique=False)
    op.create_index(op.f('ix_name_feedbacks_thread_id'), 'name_feedbacks', ['thread_id'], unique=False)
    op.create_index(op.f('ix_name_feedbacks_user_id'), 'name_feedbacks', ['user_id'], unique=False)

    op.create_table(
        'usage_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('usage_type', sa.String(length=50), nullable=False),
        sa.Column('cost_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('before_quota', sa.Integer(), nullable=False),
        sa.Column('after_quota', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['record_id'], ['name_records.id'], name=op.f('fk_usage_records_record_id_name_records')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_usage_records_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_usage_records'))
    )
    op.create_index(op.f('ix_usage_records_record_id'), 'usage_records', ['record_id'], unique=False)
    op.create_index(op.f('ix_usage_records_user_id'), 'usage_records', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_usage_records_user_id'), table_name='usage_records')
    op.drop_index(op.f('ix_usage_records_record_id'), table_name='usage_records')
    op.drop_table('usage_records')

    op.drop_index(op.f('ix_name_feedbacks_user_id'), table_name='name_feedbacks')
    op.drop_index(op.f('ix_name_feedbacks_thread_id'), table_name='name_feedbacks')
    op.drop_index(op.f('ix_name_feedbacks_record_id'), table_name='name_feedbacks')
    op.drop_table('name_feedbacks')

    op.drop_index(op.f('ix_knowledge_files_user_id'), table_name='knowledge_files')
    op.drop_index(op.f('ix_knowledge_files_status'), table_name='knowledge_files')
    op.drop_table('knowledge_files')

    op.drop_index(op.f('ix_name_records_user_id'), table_name='name_records')
    op.drop_index(op.f('ix_name_records_thread_id'), table_name='name_records')
    op.drop_index(op.f('ix_name_records_status'), table_name='name_records')
    op.drop_index(op.f('ix_name_records_is_deleted'), table_name='name_records')
    op.drop_index(op.f('ix_name_records_category'), table_name='name_records')
    op.drop_table('name_records')