"""enhance orders state machine

Revision ID: a4d8e1c6b2f0
Revises: f3c7b2a1e9d4
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4d8e1c6b2f0"
down_revision: Union[str, None] = "f3c7b2a1e9d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("product_id", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("status_reason", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("expire_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("failed_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("closed_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("refunded_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_orders_product_id"), "orders", ["product_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_orders_product_id_products"),
        "orders",
        "products",
        ["product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_orders_product_id_products"), "orders", type_="foreignkey")
    op.drop_index(op.f("ix_orders_product_id"), table_name="orders")
    op.drop_column("orders", "refunded_at")
    op.drop_column("orders", "closed_at")
    op.drop_column("orders", "failed_at")
    op.drop_column("orders", "expire_at")
    op.drop_column("orders", "status_reason")
    op.drop_column("orders", "product_id")
