"""add reports

Revision ID: e8c1f4b6a9d3
Revises: d7a5c3e9f0b1
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8c1f4b6a9d3"
down_revision: Union[str, None] = "d7a5c3e9f0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("report_version", sa.String(length=20), server_default="v1", nullable=False),
        sa.Column("data_source", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["name_candidates.id"], name=op.f("fk_report_tasks_candidate_id_name_candidates")),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_report_tasks_record_id_name_records")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_report_tasks_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report_tasks")),
    )
    op.create_index(op.f("ix_report_tasks_candidate_id"), "report_tasks", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_report_tasks_record_id"), "report_tasks", ["record_id"], unique=False)
    op.create_index(op.f("ix_report_tasks_report_version"), "report_tasks", ["report_version"], unique=False)
    op.create_index(op.f("ix_report_tasks_status"), "report_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_report_tasks_user_id"), "report_tasks", ["user_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("report_version", sa.String(length=20), server_default="v1", nullable=False),
        sa.Column("data_source", sa.JSON(), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["name_candidates.id"], name=op.f("fk_reports_candidate_id_name_candidates")),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_reports_record_id_name_records")),
        sa.ForeignKeyConstraint(["task_id"], ["report_tasks.id"], name=op.f("fk_reports_task_id_report_tasks")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_reports_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index(op.f("ix_reports_candidate_id"), "reports", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_reports_record_id"), "reports", ["record_id"], unique=False)
    op.create_index(op.f("ix_reports_report_version"), "reports", ["report_version"], unique=False)
    op.create_index(op.f("ix_reports_task_id"), "reports", ["task_id"], unique=False)
    op.create_index(op.f("ix_reports_user_id"), "reports", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_user_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_task_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_report_version"), table_name="reports")
    op.drop_index(op.f("ix_reports_record_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_candidate_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_report_tasks_user_id"), table_name="report_tasks")
    op.drop_index(op.f("ix_report_tasks_status"), table_name="report_tasks")
    op.drop_index(op.f("ix_report_tasks_report_version"), table_name="report_tasks")
    op.drop_index(op.f("ix_report_tasks_record_id"), table_name="report_tasks")
    op.drop_index(op.f("ix_report_tasks_candidate_id"), table_name="report_tasks")
    op.drop_table("report_tasks")
