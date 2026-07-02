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


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    pay_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    business_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    quota_delta: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    before_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
