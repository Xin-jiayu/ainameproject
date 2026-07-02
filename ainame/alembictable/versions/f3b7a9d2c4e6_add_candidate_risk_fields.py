"""add candidate risk fields

Revision ID: f3b7a9d2c4e6
Revises: e8a4d6c9b2f1
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3b7a9d2c4e6"
down_revision: Union[str, None] = "e8a4d6c9b2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("name_candidates", sa.Column("risk_level", sa.String(length=20), nullable=True))
    op.add_column("name_candidates", sa.Column("risk_reason", sa.Text(), nullable=True))
    op.create_index(op.f("ix_name_candidates_risk_level"), "name_candidates", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_name_candidates_risk_level"), table_name="name_candidates")
    op.drop_column("name_candidates", "risk_reason")
    op.drop_column("name_candidates", "risk_level")
