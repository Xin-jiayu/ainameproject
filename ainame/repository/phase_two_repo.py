from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import (
    DomainCheck,
    NameCandidate,
    NameRecord,
    Order,
    SocialNameCheck,
    TrademarkCheck,
)
from models.user import User
from repository.entitlement_repo import EntitlementRepository


def _json_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


class PhaseTwoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_candidates_from_result(self, record_id: int, result_data: dict[str, Any]):
        names = result_data.get("names") or []
        candidates = []
        for item in names:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            candidate = NameCandidate(
                record_id=int(record_id),
                name=item.get("name"),
                reference=item.get("reference"),
                moral=item.get("moral"),
                reason=item.get("reason") or item.get("moral"),
                domain=item.get("domain"),
                domain_status=item.get("domain_status"),
                score=item.get("score"),
                score_detail=_json_dict(item.get("score_detail")),
                score_reason=item.get("score_reason"),
                risk_level=item.get("risk_level"),
                risk_reason=item.get("risk_reason"),
            )
            self.session.add(candidate)
            candidates.append(candidate)
        await self.session.commit()
        for candidate in candidates:
            await self.session.refresh(candidate)
        return candidates

    async def replace_candidates_from_result(self, record_id: int, result_data: dict[str, Any]):
        for model in (DomainCheck, TrademarkCheck, SocialNameCheck):
            existing_checks = await self.session.execute(select(model).where(model.record_id == int(record_id)))
            for check in existing_checks.scalars().all():
                await self.session.delete(check)
        existing = await self.session.execute(select(NameCandidate).where(NameCandidate.record_id == int(record_id)))
        for candidate in existing.scalars().all():
            await self.session.delete(candidate)
        await self.session.flush()
        return await self.create_candidates_from_result(record_id, result_data)

    async def list_candidates(self, user_id: int, record_id: int):
        await self._get_user_record_or_none(user_id, record_id, raise_if_missing=True)
        result = await self.session.execute(
            select(NameCandidate)
            .where(NameCandidate.record_id == int(record_id))
            .order_by(NameCandidate.id)
        )
        return result.scalars().all()

    async def get_candidate_for_user(self, user_id: int, candidate_id: int):
        stmt = (
            select(NameCandidate)
            .join(NameRecord, NameRecord.id == NameCandidate.record_id)
            .where(
                NameCandidate.id == int(candidate_id),
                NameRecord.user_id == int(user_id),
                NameRecord.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_candidate_favorite(self, user_id: int, candidate_id: int, is_favorite: bool):
        candidate = await self.get_candidate_for_user(user_id, candidate_id)
        if not candidate:
            return None
        candidate.is_favorite = is_favorite
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def select_candidate(self, user_id: int, candidate_id: int):
        candidate = await self.get_candidate_for_user(user_id, candidate_id)
        if not candidate:
            return None
        siblings = await self.session.execute(
            select(NameCandidate).where(NameCandidate.record_id == candidate.record_id)
        )
        for item in siblings.scalars().all():
            item.is_selected = item.id == candidate.id
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def update_candidate_score(
        self,
        user_id: int,
        candidate_id: int,
        score: int,
        score_detail: dict[str, int] | None = None,
        score_reason: str | None = None,
    ):
        candidate = await self.get_candidate_for_user(user_id, candidate_id)
        if not candidate:
            return None
        candidate.score = score
        if score_detail is not None:
            candidate.score_detail = _json_dict(score_detail)
        if score_reason is not None:
            candidate.score_reason = score_reason
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def save_domain_checks(self, user_id: int, record_id: int, checks: list[dict[str, Any]]):
        await self._get_user_record_or_none(user_id, record_id, raise_if_missing=True)
        existing = await self.session.execute(select(DomainCheck).where(DomainCheck.record_id == int(record_id)))
        for check in existing.scalars().all():
            await self.session.delete(check)
        await self.session.flush()
        saved = []
        for item in checks:
            check = DomainCheck(**item)
            self.session.add(check)
            saved.append(check)
        await self.session.commit()
        for check in saved:
            await self.session.refresh(check)
        return saved

    async def list_domain_checks(self, user_id: int, record_id: int):
        await self._get_user_record_or_none(user_id, record_id, raise_if_missing=True)
        result = await self.session.execute(
            select(DomainCheck)
            .where(DomainCheck.record_id == int(record_id))
            .order_by(DomainCheck.candidate_id, DomainCheck.suffix, desc(DomainCheck.checked_at))
        )
        return result.scalars().all()

    async def create_trademark_checks(self, user_id: int, record_id: int):
        candidates = await self.list_candidates(user_id, record_id)
        existing = await self.session.execute(select(TrademarkCheck).where(TrademarkCheck.record_id == int(record_id)))
        for check in existing.scalars().all():
            await self.session.delete(check)
        await self.session.flush()
        saved = []
        for candidate in candidates:
            risk_level = self._mock_risk_level(candidate.name)
            check = TrademarkCheck(
                record_id=int(record_id),
                candidate_id=candidate.id,
                name=candidate.name,
                category_code="35",
                risk_level=risk_level,
                matched_items={"mock": True, "matches": [] if risk_level == "low" else [candidate.name]},
                provider="mock",
            )
            self.session.add(check)
            saved.append(check)
        await self.session.commit()
        for check in saved:
            await self.session.refresh(check)
        return saved

    async def list_trademark_checks(self, user_id: int, record_id: int):
        await self._get_user_record_or_none(user_id, record_id, raise_if_missing=True)
        result = await self.session.execute(
            select(TrademarkCheck)
            .where(TrademarkCheck.record_id == int(record_id))
            .order_by(TrademarkCheck.candidate_id, desc(TrademarkCheck.checked_at))
        )
        return result.scalars().all()

    async def create_social_checks(self, user_id: int, record_id: int):
        candidates = await self.list_candidates(user_id, record_id)
        existing = await self.session.execute(select(SocialNameCheck).where(SocialNameCheck.record_id == int(record_id)))
        for check in existing.scalars().all():
            await self.session.delete(check)
        await self.session.flush()
        platforms = ["wechat", "douyin", "xiaohongshu", "weibo"]
        saved = []
        for candidate in candidates:
            for platform in platforms:
                risk_level = self._mock_risk_level(f"{platform}:{candidate.name}")
                check = SocialNameCheck(
                    record_id=int(record_id),
                    candidate_id=candidate.id,
                    platform=platform,
                    name=candidate.name,
                    risk_level=risk_level,
                    matched_accounts={
                        "mock": True,
                        "accounts": [] if risk_level == "low" else [{"name": candidate.name, "platform": platform}],
                    },
                )
                self.session.add(check)
                saved.append(check)
        await self.session.commit()
        for check in saved:
            await self.session.refresh(check)
        return saved

    async def list_social_checks(self, user_id: int, record_id: int):
        await self._get_user_record_or_none(user_id, record_id, raise_if_missing=True)
        result = await self.session.execute(
            select(SocialNameCheck)
            .where(SocialNameCheck.record_id == int(record_id))
            .order_by(SocialNameCheck.candidate_id, SocialNameCheck.platform, desc(SocialNameCheck.checked_at))
        )
        return result.scalars().all()

    async def create_order(
        self,
        user_id: int,
        product_type: str,
        amount: float,
        quota_delta: int,
        business_id: int | None = None,
        extra_data: dict[str, Any] | None = None,
    ):
        order = Order(
            user_id=int(user_id),
            order_no=f"NO{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8]}",
            product_type=product_type,
            amount=Decimal(str(amount)),
            pay_status="pending",
            business_id=business_id,
            quota_delta=quota_delta,
            extra_data=extra_data,
        )
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def list_orders(self, user_id: int, skip: int = 0, limit: int = 20):
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == int(user_id))
            .order_by(desc(Order.created_at), desc(Order.id))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_order(self, user_id: int, order_id: int):
        result = await self.session.execute(
            select(Order).where(Order.id == int(order_id), Order.user_id == int(user_id))
        )
        return result.scalar_one_or_none()

    async def mark_order_paid(self, user_id: int, order_id: int):
        order = await self.get_order(user_id, order_id)
        if not order:
            return None
        if order.pay_status == "paid":
            return order

        user = await self.session.scalar(select(User).where(User.id == int(user_id)).with_for_update())
        if not user:
            return None
        before_quota = user.free_quota
        if order.quota_delta > 0:
            await EntitlementRepository(self.session).grant(
                user_id=user_id,
                entitlement_type="quota",
                amount=order.quota_delta,
                source="phase2_order_paid",
                order_id=order.id,
                remark=f"phase2 order {order.order_no} paid",
                commit=False,
            )
        order.before_quota = before_quota
        order.after_quota = user.free_quota
        order.pay_status = "paid"
        order.paid_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def _get_user_record_or_none(self, user_id: int, record_id: int, raise_if_missing: bool = False):
        result = await self.session.execute(
            select(NameRecord).where(
                NameRecord.id == int(record_id),
                NameRecord.user_id == int(user_id),
                NameRecord.is_deleted.is_(False),
            )
        )
        record = result.scalar_one_or_none()
        if raise_if_missing and not record:
            raise ValueError("record not found")
        return record

    def _mock_risk_level(self, value: str):
        bucket = sum(ord(char) for char in value) % 10
        if bucket <= 5:
            return "low"
        if bucket <= 8:
            return "medium"
        return "high"
