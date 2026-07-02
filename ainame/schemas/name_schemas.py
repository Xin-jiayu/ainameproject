from datetime import datetime
from typing import Annotated, Any, List, Literal, TypeAlias

from pydantic import BaseModel, Field, field_validator, model_validator


RiskLevel: TypeAlias = Literal["low", "medium", "high", "unknown"]


class ScoreDetailSchema(BaseModel):
    brand_sense: int = Field(..., ge=0, le=100, description="品牌感/命名质感")
    memorability: int = Field(..., ge=0, le=100, description="记忆度")
    differentiation: int = Field(..., ge=0, le=100, description="差异化")
    fit: int = Field(..., ge=0, le=100, description="匹配度")
    spreadability: int = Field(..., ge=0, le=100, description="可传播性")
    phonology: int | None = Field(default=None, ge=0, le=100, description="人名专用：音韵顺口度")
    meaning: int | None = Field(default=None, ge=0, le=100, description="人名专用：寓意质量")
    surname_fit: int | None = Field(default=None, ge=0, le=100, description="人名专用：姓氏匹配度")
    industry_fit: int | None = Field(default=None, ge=0, le=100, description="企业名专用：行业匹配度")
    cuteness: int | None = Field(default=None, ge=0, le=100, description="宠物/IP 专用：可爱度")
    imagery: int | None = Field(default=None, ge=0, le=100, description="宠物/IP 专用：画面感")
    callability: int | None = Field(default=None, ge=0, le=100, description="宠物/IP 专用：呼喊顺口度")


def _score_detail_to_dict(value: ScoreDetailSchema | dict[str, int] | None) -> dict[str, int] | None:
    if value is None:
        return None
    if isinstance(value, ScoreDetailSchema):
        return value.model_dump()
    return value


def _calculate_composite_score(score_detail: ScoreDetailSchema | dict[str, int] | None) -> int | None:
    detail = _score_detail_to_dict(score_detail)
    if not detail:
        return None
    weights = {
        "brand_sense": 0.2,
        "memorability": 0.2,
        "differentiation": 0.2,
        "fit": 0.25,
        "spreadability": 0.15,
    }
    return round(sum(max(0, min(100, int(detail.get(key, 0)))) * weight for key, weight in weights.items()))


class BaseNameCandidateSchema(BaseModel):
    name: Annotated[str, Field(..., description="候选名")]
    reference: Annotated[str, Field(..., description="出处、灵感来源或命名依据")]
    moral: Annotated[str, Field(..., description="寓意与解释")]


class HumanNameSchema(BaseNameCandidateSchema):
    domain: str | None = Field(default=None, description="兼容前端字段；人名场景不强制域名")
    domain_status: str | None = Field(default=None, description="兼容前端字段；人名场景不强制域名状态")
    score: int | None = Field(default=None, ge=0, le=100, description="兼容前端字段；综合评分，0-100")
    score_detail: ScoreDetailSchema | None = Field(default=None, description="兼容前端字段；评分明细")
    score_reason: str | None = Field(default=None, description="兼容前端字段；评分理由")
    risk_level: RiskLevel | None = Field(default=None, description="兼容前端字段；人名场景可为空")
    risk_reason: str | None = Field(default=None, description="兼容前端字段；人名场景可为空")

    @model_validator(mode="after")
    def fill_score_from_detail(self):
        if self.score is None:
            self.score = _calculate_composite_score(self.score_detail)
        return self


class PetNameSchema(BaseNameCandidateSchema):
    domain: str | None = Field(default=None, description="兼容前端字段；宠物/IP 场景不强制域名")
    domain_status: str | None = Field(default=None, description="兼容前端字段；宠物/IP 场景不强制域名状态")
    score: int | None = Field(default=None, ge=0, le=100, description="兼容前端字段；综合评分，0-100")
    score_detail: ScoreDetailSchema | None = Field(default=None, description="兼容前端字段；评分明细")
    score_reason: str | None = Field(default=None, description="兼容前端字段；评分理由")
    risk_level: RiskLevel | None = Field(default=None, description="兼容前端字段；宠物/IP 场景可为空")
    risk_reason: str | None = Field(default=None, description="兼容前端字段；宠物/IP 场景可为空")

    @model_validator(mode="after")
    def fill_score_from_detail(self):
        if self.score is None:
            self.score = _calculate_composite_score(self.score_detail)
        return self


class CompanyNameSchema(BaseNameCandidateSchema):
    domain: str = Field(..., description="为品牌设计的纯小写.com域名，例如：astar.com")
    domain_status: str | None = Field(default=None, description="域名注册状态")
    risk_level: RiskLevel | None = Field(default="unknown", description="初步命名风险等级")
    risk_reason: str | None = Field(default=None, description="初步风险说明")
    score: int = Field(..., ge=0, le=100, description="综合评分，0-100")
    score_detail: ScoreDetailSchema = Field(..., description="可解释评分维度，每项 0-100")
    score_reason: str = Field(..., description="评分理由")

    @model_validator(mode="after")
    def fill_score_from_detail(self):
        if self.score is None:
            self.score = _calculate_composite_score(self.score_detail)
        return self


class NameSchema(HumanNameSchema):
    """前端兼容 schema：保留旧字段，并接收三类命名结果的公共超集。"""

    name: Annotated[str, Field(..., description="The name of the person")]
    reference: Annotated[str, Field(..., description="The name of the person from where")]
    moral: Annotated[str, Field(..., description="寓意")]
    # 企业/品牌名可返回域名建议；人名、宠物名等非品牌场景可为空。
    domain: str | None = Field(default=None, description="为品牌设计的纯小写.com域名，例如：astar.com；非品牌场景可为空")
    # 域名注册状态仅在存在 domain 时查询；非品牌场景可为空。
    domain_status: str | None = Field(default=None, description="域名的注册状态；非品牌场景可为空")
    score: int | None = Field(default=None, ge=0, le=100, description="综合评分，0-100")
    score_detail: ScoreDetailSchema | None = Field(default=None, description="可解释评分维度，每项 0-100")
    score_reason: str | None = Field(default=None, description="评分理由")
    risk_level: RiskLevel | None = Field(default=None, description="风险等级；非企业名场景可为空")
    risk_reason: str | None = Field(default=None, description="风险说明；非企业名场景可为空")

    @field_validator("score_detail")
    @classmethod
    def validate_score_detail(cls, value):
        if value is None:
            return value
        return value

    @model_validator(mode="after")
    def fill_score_from_detail(self):
        if self.score is None:
            self.score = _calculate_composite_score(self.score_detail)
        return self


# 我们给大模型一个要求，让他起名字，一次性起多个名字。所以结构如下
class NameResultSchema(BaseModel):
    names: List[NameSchema]


class HumanNameResultSchema(BaseModel):
    names: List[HumanNameSchema]


class PetNameResultSchema(BaseModel):
    names: List[PetNameSchema]


class CompanyNameResultSchema(BaseModel):
    names: List[CompanyNameSchema]


CategoryLiteral = Literal["人名", "企业名", "宠物名"]
FrontendCategoryLiteral = Literal["brand", "person", "pet"]


# 为了多类型起名改造用户输入，接收分类参数
class NameIn(BaseModel):
    category: Annotated[CategoryLiteral | FrontendCategoryLiteral, Field(..., description="命名的分类")]
    surname: Annotated[str, Field("", description="The surname of the person")]
    gender: Annotated[Literal["不限", "男", "女"], Field("不限", description="The gender of the person")]
    length: Annotated[str, Field("", description="The length of the person")]
    other: Annotated[str | None, Field("", description="The other person")]
    exclude: Annotated[list[str], Field(default_factory=list, description="The exclude person")]
    subject: str | None = Field(default=None, description="Frontend demo naming subject")
    industry: str | None = Field(default=None, description="Frontend demo industry or scene")
    tones: list[str] = Field(default_factory=list, description="Frontend demo tone tags")
    requirements: str | None = Field(default=None, description="Frontend demo extra requirements")

    @model_validator(mode="after")
    def validate(self):
        category_map = {"brand": "企业名", "person": "人名", "pet": "宠物名"}
        self.category = category_map.get(self.category, self.category)

        if not self.other:
            parts = [
                self.subject,
                self.industry,
                "、".join(self.tones) if self.tones else None,
                self.requirements,
            ]
            self.other = "；".join(part for part in parts if part)

        if self.category == "人名" and not self.surname and self.subject:
            subject = self.subject.strip()
            surname_marker_index = subject.find("姓")
            if surname_marker_index > 0:
                self.surname = subject[surname_marker_index - 1]

        if self.category == "人名" and not self.surname:
            raise ValueError("给人起名字时，必须给定姓氏")
        # 因为用户调用NameIn，必定期望返回的是本对象。
        return self


class NameOutSchema(BaseModel):
    names: List[NameSchema]


class NameSchemaWithThreadOut(BaseModel):
    thread_id: str
    names: List[NameSchema]
    record_id: int | None = None


class NameTaskSubmitOut(BaseModel):
    task_id: str
    status: str
    message: str = "任务已提交"


class NameTaskOut(BaseModel):
    task_id: str
    status: str
    category: str
    record_id: int | None = None
    thread_id: str | None = None
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int = 0
    before_quota: int | None = None
    after_quota: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# 为了调整需求，开发一个接收参数的类
class FeedbackSchema(BaseModel):
    thread_id: str = Field(...)
    category: CategoryLiteral | FrontendCategoryLiteral | None = Field(default=None, description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，如：换成带水字旁的字")
    history_names: str | None = Field(default=None, description="上一轮候选名摘要，后端反馈续写时注入")

    @model_validator(mode="after")
    def normalize_category(self):
        category_map = {"brand": "企业名", "person": "人名", "pet": "宠物名"}
        if self.category:
            self.category = category_map.get(self.category, self.category)
        return self


class NameFeedbackOutSchema(BaseModel):
    id: int
    thread_id: str
    feedback_text: str
    result_data: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NameRecordListItemSchema(BaseModel):
    id: int
    category: CategoryLiteral
    title: str | None = None
    thread_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NameRecordDetailSchema(BaseModel):
    id: int
    category: CategoryLiteral
    title: str | None = None
    input_data: dict[str, Any]
    result_data: dict[str, Any] | None = None
    thread_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    feedbacks: list[NameFeedbackOutSchema] = []

    model_config = {"from_attributes": True}


class DeleteRecordOut(BaseModel):
    message: str


class NameCandidateOutSchema(BaseModel):
    id: int
    record_id: int
    name: str
    reference: str | None = None
    moral: str | None = None
    reason: str | None = None
    domain: str | None = None
    domain_status: str | None = None
    score: int | None = None
    score_detail: ScoreDetailSchema | None = None
    score_reason: str | None = None
    risk_level: RiskLevel | None = None
    risk_reason: str | None = None
    is_selected: bool = False
    is_favorite: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateScoreIn(BaseModel):
    score: int = Field(..., ge=0, le=100)
    score_detail: ScoreDetailSchema | None = None
    score_reason: str | None = None

    @field_validator("score_detail")
    @classmethod
    def validate_score_detail(cls, value):
        if value is None:
            return value
        return value


class DomainCheckOutSchema(BaseModel):
    id: int
    record_id: int
    candidate_id: int | None = None
    domain: str
    suffix: str
    check_status: str
    raw_result: dict[str, Any] | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}


class TrademarkCheckOutSchema(BaseModel):
    id: int
    record_id: int
    candidate_id: int | None = None
    name: str
    category_code: str | None = None
    risk_level: str
    matched_items: dict[str, Any] | None = None
    provider: str | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}


class SocialNameCheckOutSchema(BaseModel):
    id: int
    record_id: int
    candidate_id: int | None = None
    platform: str
    name: str
    risk_level: str
    matched_accounts: dict[str, Any] | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}


class OrderCreateIn(BaseModel):
    product_type: str = Field(..., max_length=50)
    amount: float = Field(0, ge=0)
    quota_delta: int = Field(0, ge=0)
    business_id: int | None = None
    extra_data: dict[str, Any] | None = None


class OrderOutSchema(BaseModel):
    id: int
    user_id: int
    order_no: str
    product_type: str
    amount: float
    pay_status: str
    business_id: int | None = None
    quota_delta: int
    before_quota: int | None = None
    after_quota: int | None = None
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    paid_at: datetime | None = None

    model_config = {"from_attributes": True}
