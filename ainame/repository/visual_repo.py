from datetime import datetime
from urllib.parse import quote_plus

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

import settings
from models.business import NameCandidate, NameRecord, VisualGenerationTask


VISUAL_PENDING = "pending"
VISUAL_PROCESSING = "processing"
VISUAL_SUCCESS = "success"
VISUAL_FAILED = "failed"
VISUAL_DELETED = "deleted"
VISUAL_STATUSES = {VISUAL_PENDING, VISUAL_PROCESSING, VISUAL_SUCCESS, VISUAL_FAILED, VISUAL_DELETED}
VISUAL_TASK_TYPES = {"logo", "brand_board", "business_card"}


class VisualGenerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        user_id: int,
        record_id: int,
        candidate_id: int | None = None,
        task_type: str = "logo",
        prompt: str | None = None,
        provider: str = "mock",
    ):
        try:
            record = await self._get_user_record(user_id, record_id)
            if not record or task_type not in VISUAL_TASK_TYPES:
                return None
            candidate = None
            if candidate_id is not None:
                candidate = await self._get_record_candidate(record_id, candidate_id)
                if not candidate:
                    return None

            candidate_name = candidate.name if candidate else self._pick_name_from_record(record)
            task = VisualGenerationTask(
                user_id=int(user_id),
                record_id=int(record_id),
                candidate_id=candidate.id if candidate else None,
                task_type=task_type,
                candidate_name=candidate_name,
                prompt=prompt or self._build_prompt(task_type, candidate_name),
                provider=provider or "mock",
                status=VISUAL_PROCESSING,
            )
            self.session.add(task)
            await self.session.flush()

            task.image_url = self._build_mock_image_url(task.id, task.task_type, task.candidate_name)
            task.status = VISUAL_SUCCESS
            task.generated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    async def list_user_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ):
        return await self._list_tasks(page=page, page_size=page_size, user_id=int(user_id), status=status)

    async def list_all_tasks(self, page: int = 1, page_size: int = 20, status: str | None = None):
        return await self._list_tasks(page=page, page_size=page_size, status=status, include_deleted=True)

    async def get_user_task(self, user_id: int, task_id: int):
        return await self.session.scalar(
            select(VisualGenerationTask).where(
                VisualGenerationTask.id == int(task_id),
                VisualGenerationTask.user_id == int(user_id),
                VisualGenerationTask.is_deleted.is_(False),
            )
        )

    async def get_task(self, task_id: int):
        return await self.session.scalar(select(VisualGenerationTask).where(VisualGenerationTask.id == int(task_id)))

    async def retry_user_task(self, user_id: int, task_id: int):
        try:
            task = await self.session.scalar(
                select(VisualGenerationTask)
                .where(
                    VisualGenerationTask.id == int(task_id),
                    VisualGenerationTask.user_id == int(user_id),
                    VisualGenerationTask.is_deleted.is_(False),
                )
                .with_for_update()
            )
            if not task:
                return None
            if task.retry_count >= settings.TASK_MAX_RETRIES:
                raise ValueError("visual task retry limit reached")

            task.status = VISUAL_PROCESSING
            task.retry_count += 1
            task.error_message = None
            task.provider = task.provider or "mock"
            task.image_url = self._build_mock_image_url(task.id, task.task_type, task.candidate_name, task.retry_count)
            task.status = VISUAL_SUCCESS
            task.generated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    async def delete_user_task(self, user_id: int, task_id: int):
        try:
            task = await self.session.scalar(
                select(VisualGenerationTask)
                .where(
                    VisualGenerationTask.id == int(task_id),
                    VisualGenerationTask.user_id == int(user_id),
                    VisualGenerationTask.is_deleted.is_(False),
                )
                .with_for_update()
            )
            if not task:
                return False
            task.is_deleted = True
            task.status = VISUAL_DELETED
            task.deleted_at = datetime.now()
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            raise

    async def _list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(VisualGenerationTask)
        list_stmt = select(VisualGenerationTask).order_by(
            desc(VisualGenerationTask.created_at), desc(VisualGenerationTask.id)
        )
        if user_id is not None:
            total_stmt = total_stmt.where(VisualGenerationTask.user_id == int(user_id))
            list_stmt = list_stmt.where(VisualGenerationTask.user_id == int(user_id))
        if status:
            total_stmt = total_stmt.where(VisualGenerationTask.status == status)
            list_stmt = list_stmt.where(VisualGenerationTask.status == status)
        if not include_deleted:
            total_stmt = total_stmt.where(VisualGenerationTask.is_deleted.is_(False))
            list_stmt = list_stmt.where(VisualGenerationTask.is_deleted.is_(False))
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    async def _get_user_record(self, user_id: int, record_id: int):
        return await self.session.scalar(
            select(NameRecord).where(
                NameRecord.id == int(record_id),
                NameRecord.user_id == int(user_id),
                NameRecord.is_deleted.is_(False),
            )
        )

    async def _get_record_candidate(self, record_id: int, candidate_id: int | None):
        if candidate_id is None:
            return None
        return await self.session.scalar(
            select(NameCandidate).where(
                NameCandidate.id == int(candidate_id),
                NameCandidate.record_id == int(record_id),
            )
        )

    def _pick_name_from_record(self, record: NameRecord):
        names = (record.result_data or {}).get("names") or []
        if names and isinstance(names[0], dict) and names[0].get("name"):
            return names[0]["name"]
        return record.title or f"record-{record.id}"

    def _build_prompt(self, task_type: str, candidate_name: str):
        prompt_map = {
            "logo": f"Logo design for {candidate_name}, clean vector style, modern brand identity.",
            "brand_board": f"Brand board for {candidate_name}, including colors, typography, and visual mood.",
            "business_card": f"Business card design for {candidate_name}, professional layout and brand mark.",
        }
        return prompt_map.get(task_type, f"Visual identity mockup for {candidate_name}.")

    def _build_mock_image_url(self, task_id: int, task_type: str, candidate_name: str, retry_count: int = 0):
        label = quote_plus(f"{candidate_name} {task_type} mock {task_id}-{retry_count}")
        return f"https://dummyimage.com/1024x1024/0f766e/ffffff&text={label}"
