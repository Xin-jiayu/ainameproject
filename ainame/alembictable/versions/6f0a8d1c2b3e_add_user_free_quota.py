"""add user free quota

Revision ID: 6f0a8d1c2b3e
Revises: 3ebdacdac34d
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f0a8d1c2b3e'
down_revision: Union[str, None] = '3ebdacdac34d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('free_quota', sa.Integer(), server_default='3', nullable=False))


def downgrade() -> None:
    op.drop_column('user', 'free_quota')
