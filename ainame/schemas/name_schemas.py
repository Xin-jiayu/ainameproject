from datetime import datetime
from typing import Annotated, Any, List, Literal

from pydantic import BaseModel, Field, model_validator


class NameSchema(BaseModel):
    name: Annotated[str, Field(..., description="The name of the person")]
    reference: Annotated[str, Field(..., description="The name of the person from where")]
    moral: Annotated[str, Field(..., description="寓意")]
    # 企业/品牌名可返回域名建议；人名、宠物名等非品牌场景可为空。
    domain: str | None = Field(default=None, description="为品牌设计的纯小写.com域名，例如：astar.com；非品牌场景可为空")
    # 域名注册状态仅在存在 domain 时查询；非品牌场景可为空。
    domain_status: str | None = Field(default=None, description="域名的注册状态；非品牌场景可为空")


# 我们给大模型一个要求，让他起名字，一次性起多个名字。所以结构如下
class NameResultSchema(BaseModel):
    names: List[NameSchema]


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


# 为了调整需求，开发一个接收参数的类
class FeedbackSchema(BaseModel):
    thread_id: str = Field(...)
    category: CategoryLiteral | FrontendCategoryLiteral | None = Field(default=None, description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，如：换成带水字旁的字")

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
