"""add social name checks

Revision ID: c4f8a2d1e9b0
Revises: b7d2e9f4a6c1
Create Date: 2026-07-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f8a2d1e9b0"
down_revision: Union[str, None] = "b7d2e9f4a6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "social_name_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("risk_level", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("matched_accounts", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["name_candidates.id"],
            name=op.f("fk_social_name_checks_candidate_id_name_candidates"),
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["name_records.id"],
            name=op.f("fk_social_name_checks_record_id_name_records"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_social_name_checks")),
    )
    op.create_index(op.f("ix_social_name_checks_candidate_id"), "social_name_checks", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_social_name_checks_name"), "social_name_checks", ["name"], unique=False)
    op.create_index(op.f("ix_social_name_checks_platform"), "social_name_checks", ["platform"], unique=False)
    op.create_index(op.f("ix_social_name_checks_record_id"), "social_name_checks", ["record_id"], unique=False)
    op.create_index(op.f("ix_social_name_checks_risk_level"), "social_name_checks", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_name_checks_risk_level"), table_name="social_name_checks")
    op.drop_index(op.f("ix_social_name_checks_record_id"), table_name="social_name_checks")
    op.drop_index(op.f("ix_social_name_checks_platform"), table_name="social_name_checks")
    op.drop_index(op.f("ix_social_name_checks_name"), table_name="social_name_checks")
    op.drop_index(op.f("ix_social_name_checks_candidate_id"), table_name="social_name_checks")
    op.drop_table("social_name_checks")
