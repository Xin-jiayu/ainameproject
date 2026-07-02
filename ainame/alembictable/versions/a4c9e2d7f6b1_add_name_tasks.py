"""add name tasks

Revision ID: a4c9e2d7f6b1
Revises: f3b7a9d2c4e6
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4c9e2d7f6b1"
down_revision: Union[str, None] = "f3b7a9d2c4e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "name_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("thread_id", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("before_quota", sa.Integer(), nullable=True),
        sa.Column("after_quota", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_name_tasks_record_id_name_records")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_name_tasks_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_name_tasks")),
        sa.UniqueConstraint("task_id", name=op.f("uq_name_tasks_task_id")),
    )
    op.create_index(op.f("ix_name_tasks_category"), "name_tasks", ["category"], unique=False)
    op.create_index(op.f("ix_name_tasks_record_id"), "name_tasks", ["record_id"], unique=False)
    op.create_index(op.f("ix_name_tasks_status"), "name_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_name_tasks_task_id"), "name_tasks", ["task_id"], unique=False)
    op.create_index(op.f("ix_name_tasks_thread_id"), "name_tasks", ["thread_id"], unique=False)
    op.create_index(op.f("ix_name_tasks_user_id"), "name_tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_name_tasks_user_id"), table_name="name_tasks")
    op.drop_index(op.f("ix_name_tasks_thread_id"), table_name="name_tasks")
    op.drop_index(op.f("ix_name_tasks_task_id"), table_name="name_tasks")
    op.drop_index(op.f("ix_name_tasks_status"), table_name="name_tasks")
    op.drop_index(op.f("ix_name_tasks_record_id"), table_name="name_tasks")
    op.drop_index(op.f("ix_name_tasks_category"), table_name="name_tasks")
    op.drop_table("name_tasks")
