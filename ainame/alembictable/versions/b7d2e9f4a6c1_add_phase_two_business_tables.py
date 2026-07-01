"""add phase two business tables

Revision ID: b7d2e9f4a6c1
Revises: 9c2a1f7e4d8b
Create Date: 2026-07-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d2e9f4a6c1"
down_revision: Union[str, None] = "9c2a1f7e4d8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_files", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("knowledge_files", sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False))
    op.add_column("knowledge_files", sa.Column("processed_at", sa.DateTime(), nullable=True))
    op.add_column("knowledge_files", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_knowledge_files_is_deleted"), "knowledge_files", ["is_deleted"], unique=False)

    op.create_table(
        "name_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("moral", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("domain_status", sa.String(length=20), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("is_favorite", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_name_candidates_record_id_name_records")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_name_candidates")),
    )
    op.create_index(op.f("ix_name_candidates_domain_status"), "name_candidates", ["domain_status"], unique=False)
    op.create_index(op.f("ix_name_candidates_is_favorite"), "name_candidates", ["is_favorite"], unique=False)
    op.create_index(op.f("ix_name_candidates_is_selected"), "name_candidates", ["is_selected"], unique=False)
    op.create_index(op.f("ix_name_candidates_name"), "name_candidates", ["name"], unique=False)
    op.create_index(op.f("ix_name_candidates_record_id"), "name_candidates", ["record_id"], unique=False)
    op.create_index(op.f("ix_name_candidates_score"), "name_candidates", ["score"], unique=False)

    op.create_table(
        "domain_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("suffix", sa.String(length=20), nullable=False),
        sa.Column("check_status", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("raw_result", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["name_candidates.id"], name=op.f("fk_domain_checks_candidate_id_name_candidates")),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_domain_checks_record_id_name_records")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_domain_checks")),
    )
    op.create_index(op.f("ix_domain_checks_candidate_id"), "domain_checks", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_domain_checks_check_status"), "domain_checks", ["check_status"], unique=False)
    op.create_index(op.f("ix_domain_checks_domain"), "domain_checks", ["domain"], unique=False)
    op.create_index(op.f("ix_domain_checks_record_id"), "domain_checks", ["record_id"], unique=False)
    op.create_index(op.f("ix_domain_checks_suffix"), "domain_checks", ["suffix"], unique=False)

    op.create_table(
        "trademark_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category_code", sa.String(length=50), nullable=True),
        sa.Column("risk_level", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("matched_items", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["name_candidates.id"], name=op.f("fk_trademark_checks_candidate_id_name_candidates")),
        sa.ForeignKeyConstraint(["record_id"], ["name_records.id"], name=op.f("fk_trademark_checks_record_id_name_records")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trademark_checks")),
    )
    op.create_index(op.f("ix_trademark_checks_candidate_id"), "trademark_checks", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_trademark_checks_category_code"), "trademark_checks", ["category_code"], unique=False)
    op.create_index(op.f("ix_trademark_checks_name"), "trademark_checks", ["name"], unique=False)
    op.create_index(op.f("ix_trademark_checks_record_id"), "trademark_checks", ["record_id"], unique=False)
    op.create_index(op.f("ix_trademark_checks_risk_level"), "trademark_checks", ["risk_level"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("product_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("pay_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=True),
        sa.Column("quota_delta", sa.Integer(), server_default="0", nullable=False),
        sa.Column("before_quota", sa.Integer(), nullable=True),
        sa.Column("after_quota", sa.Integer(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_orders_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("order_no", name=op.f("uq_orders_order_no")),
    )
    op.create_index(op.f("ix_orders_business_id"), "orders", ["business_id"], unique=False)
    op.create_index(op.f("ix_orders_order_no"), "orders", ["order_no"], unique=False)
    op.create_index(op.f("ix_orders_pay_status"), "orders", ["pay_status"], unique=False)
    op.create_index(op.f("ix_orders_product_type"), "orders", ["product_type"], unique=False)
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_product_type"), table_name="orders")
    op.drop_index(op.f("ix_orders_pay_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_business_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_trademark_checks_risk_level"), table_name="trademark_checks")
    op.drop_index(op.f("ix_trademark_checks_record_id"), table_name="trademark_checks")
    op.drop_index(op.f("ix_trademark_checks_name"), table_name="trademark_checks")
    op.drop_index(op.f("ix_trademark_checks_category_code"), table_name="trademark_checks")
    op.drop_index(op.f("ix_trademark_checks_candidate_id"), table_name="trademark_checks")
    op.drop_table("trademark_checks")

    op.drop_index(op.f("ix_domain_checks_suffix"), table_name="domain_checks")
    op.drop_index(op.f("ix_domain_checks_record_id"), table_name="domain_checks")
    op.drop_index(op.f("ix_domain_checks_domain"), table_name="domain_checks")
    op.drop_index(op.f("ix_domain_checks_check_status"), table_name="domain_checks")
    op.drop_index(op.f("ix_domain_checks_candidate_id"), table_name="domain_checks")
    op.drop_table("domain_checks")

    op.drop_index(op.f("ix_name_candidates_score"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_record_id"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_name"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_is_selected"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_is_favorite"), table_name="name_candidates")
    op.drop_index(op.f("ix_name_candidates_domain_status"), table_name="name_candidates")
    op.drop_table("name_candidates")

    op.drop_index(op.f("ix_knowledge_files_is_deleted"), table_name="knowledge_files")
    op.drop_column("knowledge_files", "deleted_at")
    op.drop_column("knowledge_files", "processed_at")
    op.drop_column("knowledge_files", "is_deleted")
    op.drop_column("knowledge_files", "retry_count")
