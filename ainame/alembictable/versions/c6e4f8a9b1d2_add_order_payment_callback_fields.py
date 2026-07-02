"""add order payment callback fields

Revision ID: c6e4f8a9b1d2
Revises: b9f2c5d7a1e3
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6e4f8a9b1d2"
down_revision: Union[str, None] = "b9f2c5d7a1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("payment_provider", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("payment_trade_no", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("payment_callback_data", sa.JSON(), nullable=True))
    op.add_column("orders", sa.Column("payment_verified_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_orders_payment_provider"), "orders", ["payment_provider"], unique=False)
    op.create_index(op.f("ix_orders_payment_trade_no"), "orders", ["payment_trade_no"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_payment_trade_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_payment_provider"), table_name="orders")
    op.drop_column("orders", "payment_verified_at")
    op.drop_column("orders", "payment_callback_data")
    op.drop_column("orders", "payment_trade_no")
    op.drop_column("orders", "payment_provider")
