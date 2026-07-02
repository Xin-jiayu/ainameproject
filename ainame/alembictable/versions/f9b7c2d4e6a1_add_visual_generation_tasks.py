"""add visual generation tasks

Revision ID: f9b7c2d4e6a1
Revises: e8c1f4b6a9d3
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9b7c2d4e6a1"
down_revision: Union[str, None] = "e8c1f4b6a9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visual_generation_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("candidate_name", sa.String(length=100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["name_candidates.id"], name=op.f("fk_visual_generation_tasks_candidate_id_name_candidates")
        ),
        sa.ForeignKeyConstraint(
            ["record_id"], ["name_records.id"], name=op.f("fk_visual_generation_tasks_record_id_name_records")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_visual_generation_tasks_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visual_generation_tasks")),
    )
    op.create_index(op.f("ix_visual_generation_tasks_candidate_id"), "visual_generation_tasks", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_is_deleted"), "visual_generation_tasks", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_provider"), "visual_generation_tasks", ["provider"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_record_id"), "visual_generation_tasks", ["record_id"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_status"), "visual_generation_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_task_type"), "visual_generation_tasks", ["task_type"], unique=False)
    op.create_index(op.f("ix_visual_generation_tasks_user_id"), "visual_generation_tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_visual_generation_tasks_user_id"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_task_type"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_status"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_record_id"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_provider"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_is_deleted"), table_name="visual_generation_tasks")
    op.drop_index(op.f("ix_visual_generation_tasks_candidate_id"), table_name="visual_generation_tasks")
    op.drop_table("visual_generation_tasks")
