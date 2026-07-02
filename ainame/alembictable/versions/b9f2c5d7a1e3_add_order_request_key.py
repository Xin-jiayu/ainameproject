"""add order request key

Revision ID: b9f2c5d7a1e3
Revises: a4d8e1c6b2f0
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9f2c5d7a1e3"
down_revision: Union[str, None] = "a4d8e1c6b2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("request_key", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_orders_request_key"), "orders", ["request_key"], unique=False)
    op.create_unique_constraint(
        "uq_orders_user_id_request_key",
        "orders",
        ["user_id", "request_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_orders_user_id_request_key", "orders", type_="unique")
    op.drop_index(op.f("ix_orders_request_key"), table_name="orders")
    op.drop_column("orders", "request_key")
