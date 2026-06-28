from datetime import datetime
from typing import Any

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import NameFeedback, NameRecord, UsageRecord


class NameRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_record(
        self,
        user_id: int,
        category: str,
        input_data: dict[str, Any],
        result_data: dict[str, Any],
        thread_id: str,
    ):
        title = self._build_title(category, input_data, result_data)
        record = NameRecord(
            user_id=int(user_id),
            category=category,
            title=title,
            input_data=input_data,
            result_data=result_data,
            thread_id=thread_id,
            status="success",
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def create_usage_record(
        self,
        user_id: int,
        record_id: int,
        usage_type: str,
        cost_count: int,
        before_quota: int,
        after_quota: int,
    ):
        usage_record = UsageRecord(
            user_id=int(user_id),
            record_id=int(record_id),
            usage_type=usage_type,
            cost_count=cost_count,
            before_quota=before_quota,
            after_quota=after_quota,
        )
        self.session.add(usage_record)
        await self.session.commit()
        await self.session.refresh(usage_record)
        return usage_record

    async def list_records(self, user_id: int, skip: int = 0, limit: int = 20):
        stmt = (
            select(NameRecord)
            .where(NameRecord.user_id == int(user_id), NameRecord.is_deleted.is_(False))
            .order_by(desc(NameRecord.updated_at), desc(NameRecord.id))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_record(self, user_id: int, record_id: int):
        stmt = select(NameRecord).where(
            NameRecord.id == int(record_id),
            NameRecord.user_id == int(user_id),
            NameRecord.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_feedbacks(self, record_id: int, user_id: int):
        stmt = (
            select(NameFeedback)
            .where(NameFeedback.record_id == int(record_id), NameFeedback.user_id == int(user_id))
            .order_by(NameFeedback.created_at, NameFeedback.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_record_by_thread_id(self, user_id: int, thread_id: str):
        stmt = select(NameRecord).where(
            NameRecord.thread_id == thread_id,
            NameRecord.user_id == int(user_id),
            NameRecord.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_feedback_and_update_record(
        self,
        record: NameRecord,
        feedback_text: str,
        result_data: dict[str, Any],
    ):
        feedback = NameFeedback(
            record_id=record.id,
            user_id=record.user_id,
            thread_id=record.thread_id,
            feedback_text=feedback_text,
            result_data=result_data,
        )
        self.session.add(feedback)
        record.result_data = result_data
        record.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(record)
        await self.session.refresh(feedback)
        return feedback

    async def delete_record(self, user_id: int, record_id: int):
        stmt = (
            update(NameRecord)
            .where(
                NameRecord.id == int(record_id),
                NameRecord.user_id == int(user_id),
                NameRecord.is_deleted.is_(False),
            )
            .values(is_deleted=True, updated_at=datetime.now())
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    def _build_title(self, category: str, input_data: dict[str, Any], result_data: dict[str, Any]):
        names = result_data.get("names") or []
        if names and isinstance(names[0], dict) and names[0].get("name"):
            return names[0]["name"]
        if category == "人名" and input_data.get("surname"):
            return f"{input_data['surname']}氏起名"
        if input_data.get("other"):
            return str(input_data["other"])[:30]
        return f"{category}起名"