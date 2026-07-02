from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    record_id: Mapped[int | None] = mapped_column(ForeignKey("name_records.id"), nullable=True, index=True)
    usage_type: Mapped[str] = mapped_column(String(50))
    cost_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    before_quota: Mapped[int] = mapped_column(Integer)
    after_quota: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class EntitlementAccount(Base):
    __tablename__ = "entitlement_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    entitlement_type: Mapped[str] = mapped_column(String(50), index=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class EntitlementRecord(Base):
    __tablename__ = "entitlement_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("entitlement_accounts.id"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)
    entitlement_type: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    change_type: Mapped[str] = mapped_column(String(20), index=True)
    change_amount: Mapped[int] = mapped_column(Integer)
    before_balance: Mapped[int] = mapped_column(Integer)
    after_balance: Mapped[int] = mapped_column(Integer)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class NameRecord(Base):
    __tablename__ = "name_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    thread_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="success", server_default="success", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class NameTask(Base):
    __tablename__ = "name_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    record_id: Mapped[int | None] = mapped_column(ForeignKey("name_records.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    before_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class NameFeedback(Base):
    __tablename__ = "name_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    feedback_text: Mapped[str] = mapped_column(Text)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class NameCandidate(Base):
    __tablename__ = "name_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    score_detail: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    risk_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class DomainCheck(Base):
    __tablename__ = "domain_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    suffix: Mapped[str] = mapped_column(String(20), index=True)
    check_status: Mapped[str] = mapped_column(String(20), default="unknown", server_default="unknown", index=True)
    raw_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TrademarkCheck(Base):
    __tablename__ = "trademark_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    category_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", server_default="unknown", index=True)
    matched_items: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SocialNameCheck(Base):
    __tablename__ = "social_name_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    platform: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", server_default="unknown", index=True)
    matched_accounts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ReportTask(Base):
    __tablename__ = "report_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    report_version: Mapped[str] = mapped_column(String(20), default="v1", server_default="v1", index=True)
    data_source: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("report_tasks.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    report_version: Mapped[str] = mapped_column(String(20), default="v1", server_default="v1", index=True)
    data_source: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class VisualGenerationTask(Base):
    __tablename__ = "visual_generation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("name_records.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("name_candidates.id"), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(50), index=True)
    candidate_name: Mapped[str] = mapped_column(String(100))
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    request_key: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    product_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    pay_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    status_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    payment_trade_no: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    payment_callback_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    payment_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    business_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    quota_delta: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    before_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expire_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    entitlement_type: Mapped[str] = mapped_column(String(50), index=True)
    entitlement_amount: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    valid_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
