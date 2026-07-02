from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductBaseIn(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    price: Decimal = Field(0, ge=0)
    entitlement_type: str = Field(..., min_length=2, max_length=50)
    entitlement_amount: int = Field(0, ge=0)
    valid_days: int | None = Field(default=None, ge=1)
    is_active: bool = True
    sort_order: int = 0


class ProductCreateIn(ProductBaseIn):
    pass


class ProductUpdateIn(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    entitlement_type: str | None = Field(default=None, min_length=2, max_length=50)
    entitlement_amount: int | None = Field(default=None, ge=0)
    valid_days: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    sort_order: int | None = None


class ProductStatusIn(BaseModel):
    is_active: bool


class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    price: Decimal
    entitlement_type: str
    entitlement_amount: int
    valid_days: int | None = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class OrderCreateFromProductIn(BaseModel):
    product_id: int = Field(..., ge=1)
    request_key: str | None = Field(default=None, min_length=8, max_length=100)


class OrderFailIn(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class AlipaySandboxSuccessIn(BaseModel):
    trade_no: str | None = Field(default=None, max_length=100)
    callback_data: dict | None = None


class AlipaySandboxFailIn(BaseModel):
    trade_no: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=255)
    callback_data: dict | None = None


class OrderCloseIn(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class CommerceOrderOut(BaseModel):
    id: int
    user_id: int
    product_id: int | None = None
    order_no: str
    request_key: str | None = None
    product_type: str
    amount: Decimal
    pay_status: str
    status_reason: str | None = None
    payment_provider: str | None = None
    payment_trade_no: str | None = None
    payment_callback_data: dict | None = None
    payment_verified_at: datetime | None = None
    business_id: int | None = None
    quota_delta: int
    before_quota: int | None = None
    after_quota: int | None = None
    extra_data: dict | None = None
    created_at: datetime
    expire_at: datetime | None = None
    paid_at: datetime | None = None
    failed_at: datetime | None = None
    closed_at: datetime | None = None
    refunded_at: datetime | None = None

    model_config = {"from_attributes": True}


class CommerceOrderListOut(BaseModel):
    items: list[CommerceOrderOut]
    total: int
    page: int
    page_size: int


class EntitlementAccountOut(BaseModel):
    id: int
    user_id: int
    entitlement_type: str
    balance: int
    valid_until: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntitlementRecordOut(BaseModel):
    id: int
    user_id: int
    account_id: int | None = None
    order_id: int | None = None
    entitlement_type: str
    source: str
    change_type: str
    change_amount: int
    before_balance: int
    after_balance: int
    valid_until: datetime | None = None
    remark: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EntitlementRecordListOut(BaseModel):
    items: list[EntitlementRecordOut]
    total: int
    page: int
    page_size: int


class AdminEntitlementAdjustIn(BaseModel):
    user_id: int = Field(..., ge=1)
    entitlement_type: str = Field(..., min_length=2, max_length=50)
    change_amount: int
    valid_days: int | None = Field(default=None, ge=1)
    remark: str | None = Field(default=None, max_length=255)


class ReportTaskCreateIn(BaseModel):
    record_id: int = Field(..., ge=1)
    candidate_id: int | None = Field(default=None, ge=1)
    report_version: str = Field(default="v1", min_length=1, max_length=20)


class ReportTaskOut(BaseModel):
    id: int
    user_id: int
    record_id: int
    candidate_id: int | None = None
    status: str
    report_version: str
    data_source: dict | None = None
    error_message: str | None = None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    record_id: int
    candidate_id: int | None = None
    report_version: str
    data_source: dict | None = None
    content: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportTaskListOut(BaseModel):
    items: list[ReportTaskOut]
    total: int
    page: int
    page_size: int


class VisualTaskCreateIn(BaseModel):
    record_id: int = Field(..., ge=1)
    candidate_id: int | None = Field(default=None, ge=1)
    task_type: str = Field(..., min_length=2, max_length=50)
    prompt: str | None = Field(default=None, max_length=2000)
    provider: str = Field(default="mock", min_length=2, max_length=50)


class VisualTaskOut(BaseModel):
    id: int
    user_id: int
    record_id: int
    candidate_id: int | None = None
    task_type: str
    candidate_name: str
    prompt: str | None = None
    image_url: str | None = None
    provider: str | None = None
    status: str
    error_message: str | None = None
    retry_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    generated_at: datetime | None = None
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class VisualTaskListOut(BaseModel):
    items: list[VisualTaskOut]
    total: int
    page: int
    page_size: int


class ProviderFailureCountOut(BaseModel):
    provider: str
    count: int


class PaymentFailureItemOut(BaseModel):
    id: int
    user_id: int
    order_no: str
    provider: str | None = None
    reason: str | None = None
    failed_at: datetime | None = None
    created_at: datetime


class ReportFailureItemOut(BaseModel):
    id: int
    user_id: int
    record_id: int
    candidate_id: int | None = None
    report_version: str
    reason: str | None = None
    updated_at: datetime
    created_at: datetime


class VisualFailureItemOut(BaseModel):
    id: int
    user_id: int
    record_id: int
    candidate_id: int | None = None
    task_type: str
    provider: str | None = None
    reason: str | None = None
    updated_at: datetime
    created_at: datetime


class PaymentFailureStatsOut(BaseModel):
    total: int
    by_provider: list[ProviderFailureCountOut]
    recent: list[PaymentFailureItemOut]


class ReportFailureStatsOut(BaseModel):
    total: int
    recent: list[ReportFailureItemOut]


class VisualFailureStatsOut(BaseModel):
    total: int
    by_provider: list[ProviderFailureCountOut]
    recent: list[VisualFailureItemOut]


class AdminCommercialFailureStatsOut(BaseModel):
    payment_failures: PaymentFailureStatsOut
    report_failures: ReportFailureStatsOut
    visual_generation_failures: VisualFailureStatsOut
