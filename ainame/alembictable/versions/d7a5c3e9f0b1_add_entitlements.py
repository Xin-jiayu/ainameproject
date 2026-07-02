"""add entitlements

Revision ID: d7a5c3e9f0b1
Revises: c6e4f8a9b1d2
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7a5c3e9f0b1"
down_revision: Union[str, None] = "c6e4f8a9b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entitlement_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entitlement_type", sa.String(length=50), nullable=False),
        sa.Column("balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_entitlement_accounts_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entitlement_accounts")),
        sa.UniqueConstraint("user_id", "entitlement_type", name="uq_entitlement_accounts_user_type"),
    )
    op.create_index(op.f("ix_entitlement_accounts_entitlement_type"), "entitlement_accounts", ["entitlement_type"], unique=False)
    op.create_index(op.f("ix_entitlement_accounts_user_id"), "entitlement_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_entitlement_accounts_valid_until"), "entitlement_accounts", ["valid_until"], unique=False)

    op.create_table(
        "entitlement_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("entitlement_type", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("change_amount", sa.Integer(), nullable=False),
        sa.Column("before_balance", sa.Integer(), nullable=False),
        sa.Column("after_balance", sa.Integer(), nullable=False),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["entitlement_accounts.id"], name=op.f("fk_entitlement_records_account_id_entitlement_accounts")),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name=op.f("fk_entitlement_records_order_id_orders")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_entitlement_records_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entitlement_records")),
    )
    op.create_index(op.f("ix_entitlement_records_account_id"), "entitlement_records", ["account_id"], unique=False)
    op.create_index(op.f("ix_entitlement_records_change_type"), "entitlement_records", ["change_type"], unique=False)
    op.create_index(op.f("ix_entitlement_records_created_at"), "entitlement_records", ["created_at"], unique=False)
    op.create_index(op.f("ix_entitlement_records_entitlement_type"), "entitlement_records", ["entitlement_type"], unique=False)
    op.create_index(op.f("ix_entitlement_records_order_id"), "entitlement_records", ["order_id"], unique=False)
    op.create_index(op.f("ix_entitlement_records_source"), "entitlement_records", ["source"], unique=False)
    op.create_index(op.f("ix_entitlement_records_user_id"), "entitlement_records", ["user_id"], unique=False)

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "insert into entitlement_accounts "
            "(user_id, entitlement_type, balance, valid_until, created_at, updated_at) "
            "select id, 'free_quota', free_quota, null, now(), now() from `user` where free_quota > 0"
        )
    )
    bind.execute(
        sa.text(
            "insert into entitlement_records "
            "(user_id, account_id, order_id, entitlement_type, source, change_type, change_amount, "
            "before_balance, after_balance, valid_until, remark, created_at) "
            "select a.user_id, a.id, null, a.entitlement_type, 'migration_initial', 'grant', "
            "a.balance, 0, a.balance, a.valid_until, 'initial free_quota migration', now() "
            "from entitlement_accounts a where a.entitlement_type = 'free_quota' and a.balance > 0"
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_entitlement_records_user_id"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_source"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_order_id"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_entitlement_type"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_created_at"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_change_type"), table_name="entitlement_records")
    op.drop_index(op.f("ix_entitlement_records_account_id"), table_name="entitlement_records")
    op.drop_table("entitlement_records")

    op.drop_index(op.f("ix_entitlement_accounts_valid_until"), table_name="entitlement_accounts")
    op.drop_index(op.f("ix_entitlement_accounts_user_id"), table_name="entitlement_accounts")
    op.drop_index(op.f("ix_entitlement_accounts_entitlement_type"), table_name="entitlement_accounts")
    op.drop_table("entitlement_accounts")
