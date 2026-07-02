from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import NameTask


class NameTaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        task_id: str,
        user_id: int,
        category: str,
        input_data: dict,
        before_quota: int | None = None,
        after_quota: int | None = None,
    ):
        task = NameTask(
            task_id=task_id,
            user_id=int(user_id),
            category=category,
            input_data=input_data,
            status="pending",
            before_quota=before_quota,
            after_quota=after_quota,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_user_task(self, user_id: int, task_id: str):
        result = await self.session.execute(
            select(NameTask).where(NameTask.task_id == task_id, NameTask.user_id == int(user_id))
        )
        return result.scalar_one_or_none()

    async def get_task_for_update(self, task_id: str):
        result = await self.session.execute(select(NameTask).where(NameTask.task_id == task_id).with_for_update())
        return result.scalar_one_or_none()

    async def mark_running(self, task_id: str):
        task = await self.get_task_for_update(task_id)
        if not task:
            return None
        if task.status not in {"pending", "failed"}:
            return task
        task.status = "running"
        task.error_message = None
        task.started_at = datetime.now()
        task.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def mark_success(self, task_id: str, record_id: int, thread_id: str, result_data: dict):
        task = await self.get_task_for_update(task_id)
        if not task:
            return None
        task.status = "success"
        task.record_id = int(record_id)
        task.thread_id = thread_id
        task.result_data = result_data
        task.error_message = None
        task.finished_at = datetime.now()
        task.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def mark_failed(self, task_id: str, error_message: str):
        task = await self.get_task_for_update(task_id)
        if not task:
            return None
        task.status = "failed"
        task.error_message = error_message
        task.retry_count = (task.retry_count or 0) + 1
        task.finished_at = datetime.now()
        task.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(task)
        return task
