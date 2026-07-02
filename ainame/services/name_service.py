import json
import uuid

import aio_pika
from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

import settings
from core.workflow import NameGenerationError
from repository.name_record_repo import NameRecordRepository
from repository.name_task_repo import NameTaskRepository
from schemas.name_schemas import (
    FeedbackSchema,
    NameIn,
    NameOutSchema,
    NameRecordDetailSchema,
    NameSchemaWithThreadOut,
    NameTaskOut,
    NameTaskSubmitOut,
)
from services.ai_service import AIService
from services.user_service import UserService


class NameService:
    """Naming workflow, async task submission, history, candidates, and usage records."""

    QUEUE_NAME = "name_generation_queue"

    def __init__(self, session: AsyncSession, ai_service: AIService | None = None):
        self.session = session
        self.ai_service = ai_service or AIService()
        self.record_repository = NameRecordRepository(session=session)
        self.task_repository = NameTaskRepository(session=session)
        self.user_service = UserService(session=session)

    async def generate_legacy_names(self, name_info: NameIn, user_id: int) -> NameOutSchema:
        quota_change = await self.user_service.consume_quota_or_raise(user_id)
        try:
            result = await self.ai_service.generate_legacy_names(name_info, user_id)
            record = await self.record_repository.create_record(
                user_id=user_id,
                category=name_info.category,
                input_data=name_info.model_dump(),
                result_data=result,
                thread_id=f"legacy-{uuid.uuid4()}",
            )
            await self.save_candidates(record.id, result)
            await self.save_usage_record(user_id, record.id, quota_change)
            return NameOutSchema(names=result["names"])
        except NameGenerationError as e:
            await self.user_service.refund_free_quota(user_id)
            raise HTTPException(status_code=502, detail=str(e))
        except Exception:
            await self.user_service.refund_free_quota(user_id)
            raise

    async def generate_names(self, name_info: NameIn, user_id: int) -> NameSchemaWithThreadOut:
        quota_change = await self.user_service.consume_quota_or_raise(user_id)
        try:
            result = await self.ai_service.generate_names(name_info, user_id)
            record = await self.record_repository.create_record(
                user_id=user_id,
                category=name_info.category,
                input_data=name_info.model_dump(),
                result_data=result["names"],
                thread_id=result["thread_id"],
            )
            await self.save_candidates(record.id, result["names"])
            await self.save_usage_record(user_id, record.id, quota_change)
            return NameSchemaWithThreadOut(
                thread_id=result["thread_id"],
                names=result["names"]["names"],
                record_id=record.id,
            )
        except NameGenerationError as e:
            await self.user_service.refund_free_quota(user_id)
            raise HTTPException(status_code=502, detail=str(e))
        except Exception:
            await self.user_service.refund_free_quota(user_id)
            raise

    async def submit_generation_task(self, name_info: NameIn, user_id: int) -> NameTaskSubmitOut:
        quota_change = await self.user_service.consume_quota_or_raise(user_id)
        task_id = uuid.uuid4().hex
        task = await self.task_repository.create_task(
            task_id=task_id,
            user_id=user_id,
            category=name_info.category,
            input_data=name_info.model_dump(),
            before_quota=quota_change["before_quota"],
            after_quota=quota_change["after_quota"],
        )
        try:
            await self.enqueue_generation_task(task.task_id)
        except Exception as exc:
            await self.user_service.refund_free_quota(user_id)
            await self.task_repository.mark_failed(task.task_id, f"enqueue failed: {exc}")
            raise HTTPException(status_code=503, detail="起名任务提交失败，请稍后重试")
        return NameTaskSubmitOut(task_id=task.task_id, status=task.status)

    async def get_generation_task(self, user_id: int, task_id: str) -> NameTaskOut:
        task = await self.task_repository.get_user_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="起名任务不存在")
        return task

    async def run_generation_task(self, task_id: str):
        task = await self.task_repository.mark_running(task_id)
        if not task:
            return None
        if task.status != "running":
            return task

        try:
            name_info = NameIn.model_validate(task.input_data)
            result = await self.ai_service.generate_names(name_info, task.user_id)
            record = await self.record_repository.create_record(
                user_id=task.user_id,
                category=name_info.category,
                input_data=task.input_data,
                result_data=result["names"],
                thread_id=result["thread_id"],
            )
            await self.save_candidates(record.id, result["names"])
            await self.save_usage_record(
                task.user_id,
                record.id,
                {
                    "before_quota": task.before_quota,
                    "after_quota": task.after_quota,
                },
            )
            return await self.task_repository.mark_success(
                task.task_id,
                record_id=record.id,
                thread_id=result["thread_id"],
                result_data=result["names"],
            )
        except Exception as exc:
            await self.user_service.refund_free_quota(task.user_id)
            return await self.task_repository.mark_failed(task.task_id, str(exc))

    async def enqueue_generation_task(self, task_id: str):
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.QUEUE_NAME, durable=True)
            body = json.dumps({"task_id": task_id}).encode("utf-8")
            await channel.default_exchange.publish(aio_pika.Message(body=body), routing_key=queue.name)

    async def list_records(self, user_id: int, skip: int = 0, limit: int = 20):
        return await self.record_repository.list_records(user_id, skip=skip, limit=limit)

    async def get_record_detail(self, user_id: int, record_id: int) -> NameRecordDetailSchema:
        record = await self.record_repository.get_record(user_id, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="起名记录不存在")
        feedbacks = await self.record_repository.list_feedbacks(record.id, user_id)
        return NameRecordDetailSchema(
            id=record.id,
            category=record.category,
            title=record.title,
            input_data=record.input_data,
            result_data=record.result_data,
            thread_id=record.thread_id,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            feedbacks=feedbacks,
        )

    async def delete_record(self, user_id: int, record_id: int) -> bool:
        deleted = await self.record_repository.delete_record(user_id, record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="起名记录不存在")
        return deleted

    async def feedback(self, data: FeedbackSchema, user_id: int) -> NameSchemaWithThreadOut:
        record = await self.record_repository.get_record_by_thread_id(user_id, data.thread_id)
        if not record:
            raise HTTPException(status_code=404, detail="起名记录不存在，无法继续优化")
        if not data.category:
            data.category = record.category
        if not data.history_names:
            data.history_names = self.format_feedback_history(record.result_data)

        try:
            result = await self.ai_service.feedback_names(data, user_id)
        except NameGenerationError as e:
            raise HTTPException(status_code=502, detail=str(e))

        await self.record_repository.add_feedback_and_update_record(
            record=record,
            feedback_text=data.feedback,
            result_data=result["names"],
        )
        await self.save_candidates(record.id, result["names"], replace=True)
        return NameSchemaWithThreadOut(
            thread_id=result["thread_id"],
            names=result["names"]["names"],
            record_id=record.id,
        )

    async def save_usage_record(self, user_id: int, record_id: int, quota_change: dict):
        await self.record_repository.create_usage_record(
            user_id=user_id,
            record_id=record_id,
            usage_type="name_generate",
            cost_count=1,
            before_quota=quota_change["before_quota"],
            after_quota=quota_change["after_quota"],
        )

    async def save_candidates(self, record_id: int, result_data: dict, replace: bool = False):
        from services.validation_service import ValidationService

        validation_service = ValidationService(session=self.session)
        if replace:
            return await validation_service.replace_candidates_from_result(record_id, result_data)
        return await validation_service.create_candidates_from_result(record_id, result_data)

    def format_feedback_history(self, result_data: dict | None) -> str:
        if not isinstance(result_data, dict):
            return ""

        names = result_data.get("names") or []
        lines = []
        for index, item in enumerate(names[:5], start=1):
            if not isinstance(item, dict) or not item.get("name"):
                continue
            parts = [f"{index}. {item.get('name')}"]
            if item.get("reference"):
                parts.append(f"来源：{item.get('reference')}")
            if item.get("moral"):
                parts.append(f"寓意：{item.get('moral')}")
            if item.get("score_reason"):
                parts.append(f"评分理由：{item.get('score_reason')}")
            lines.append("；".join(parts))
        return "\n".join(lines)
