"""add candidate score details

Revision ID: e8a4d6c9b2f1
Revises: d1a9c7e5f2b4
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8a4d6c9b2f1"
down_revision: Union[str, None] = "d1a9c7e5f2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("name_candidates", sa.Column("score_detail", sa.JSON(), nullable=True))
    op.add_column("name_candidates", sa.Column("score_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("name_candidates", "score_reason")
    op.drop_column("name_candidates", "score_detail")
