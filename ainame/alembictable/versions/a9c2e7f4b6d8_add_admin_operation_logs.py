"""add admin operation logs

Revision ID: a9c2e7f4b6d8
Revises: f9b7c2d4e6a1
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9c2e7f4b6d8"
down_revision: Union[str, None] = "f9b7c2d4e6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_operation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["user.id"], name=op.f("fk_admin_operation_logs_admin_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_operation_logs")),
    )
    op.create_index(op.f("ix_admin_operation_logs_action"), "admin_operation_logs", ["action"], unique=False)
    op.create_index(op.f("ix_admin_operation_logs_admin_user_id"), "admin_operation_logs", ["admin_user_id"], unique=False)
    op.create_index(op.f("ix_admin_operation_logs_created_at"), "admin_operation_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_admin_operation_logs_resource_id"), "admin_operation_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_admin_operation_logs_resource_type"), "admin_operation_logs", ["resource_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_operation_logs_resource_type"), table_name="admin_operation_logs")
    op.drop_index(op.f("ix_admin_operation_logs_resource_id"), table_name="admin_operation_logs")
    op.drop_index(op.f("ix_admin_operation_logs_created_at"), table_name="admin_operation_logs")
    op.drop_index(op.f("ix_admin_operation_logs_admin_user_id"), table_name="admin_operation_logs")
    op.drop_index(op.f("ix_admin_operation_logs_action"), table_name="admin_operation_logs")
    op.drop_table("admin_operation_logs")
