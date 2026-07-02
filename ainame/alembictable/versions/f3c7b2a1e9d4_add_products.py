"""add products

Revision ID: f3c7b2a1e9d4
Revises: e2b6a4c9d8f1
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from datetime import datetime
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3c7b2a1e9d4"
down_revision: Union[str, None] = "e2b6a4c9d8f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("entitlement_type", sa.String(length=50), nullable=False),
        sa.Column("entitlement_amount", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("code", name=op.f("uq_products_code")),
    )
    op.create_index(op.f("ix_products_code"), "products", ["code"], unique=True)
    op.create_index(op.f("ix_products_entitlement_type"), "products", ["entitlement_type"], unique=False)
    op.create_index(op.f("ix_products_is_active"), "products", ["is_active"], unique=False)
    op.create_index(op.f("ix_products_sort_order"), "products", ["sort_order"], unique=False)

    products = [
        {
            "code": "free_trial",
            "name": "免费体验包",
            "description": "用于新用户体验基础起名能力",
            "price": 0,
            "entitlement_type": "free_quota",
            "entitlement_amount": 3,
            "valid_days": None,
            "is_active": 1,
            "sort_order": 10,
        },
        {
            "code": "quota_20",
            "name": "20次起名包",
            "description": "购买后增加20次可用起名权益",
            "price": 19.90,
            "entitlement_type": "quota",
            "entitlement_amount": 20,
            "valid_days": 365,
            "is_active": 1,
            "sort_order": 20,
        },
        {
            "code": "member_monthly",
            "name": "月度会员",
            "description": "30天会员权益，适合持续命名和品牌方案优化",
            "price": 39.90,
            "entitlement_type": "membership_days",
            "entitlement_amount": 30,
            "valid_days": 30,
            "is_active": 1,
            "sort_order": 30,
        },
    ]
    products_table = sa.table(
        "products",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("price", sa.Numeric),
        sa.column("entitlement_type", sa.String),
        sa.column("entitlement_amount", sa.Integer),
        sa.column("valid_days", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    now = datetime.now()
    op.bulk_insert(
        products_table,
        [
            {
                **item,
                "created_at": now,
                "updated_at": now,
            }
            for item in products
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_products_sort_order"), table_name="products")
    op.drop_index(op.f("ix_products_is_active"), table_name="products")
    op.drop_index(op.f("ix_products_entitlement_type"), table_name="products")
    op.drop_index(op.f("ix_products_code"), table_name="products")
    op.drop_table("products")
