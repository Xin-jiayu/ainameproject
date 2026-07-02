from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import Order, ReportTask, VisualGenerationTask
from repository.commerce_repo import ORDER_FAILED
from repository.report_repo import REPORT_FAILED
from repository.visual_repo import VISUAL_FAILED


class AdminCommercialStatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_failure_stats(self, recent_limit: int = 10):
        recent_limit = min(max(recent_limit, 1), 50)
        return {
            "payment_failures": await self._payment_failure_stats(recent_limit),
            "report_failures": await self._report_failure_stats(recent_limit),
            "visual_generation_failures": await self._visual_failure_stats(recent_limit),
        }

    async def _payment_failure_stats(self, recent_limit: int):
        total = await self.session.scalar(
            select(func.count()).select_from(Order).where(Order.pay_status == ORDER_FAILED)
        )
        provider_rows = await self.session.execute(
            select(Order.payment_provider, func.count())
            .where(Order.pay_status == ORDER_FAILED)
            .group_by(Order.payment_provider)
            .order_by(desc(func.count()))
        )
        recent_rows = await self.session.execute(
            select(Order)
            .where(Order.pay_status == ORDER_FAILED)
            .order_by(desc(Order.failed_at), desc(Order.id))
            .limit(recent_limit)
        )
        return {
            "total": total or 0,
            "by_provider": [
                {"provider": provider or "unknown", "count": count} for provider, count in provider_rows.all()
            ],
            "recent": [
                {
                    "id": order.id,
                    "user_id": order.user_id,
                    "order_no": order.order_no,
                    "provider": order.payment_provider,
                    "reason": order.status_reason,
                    "failed_at": order.failed_at,
                    "created_at": order.created_at,
                }
                for order in recent_rows.scalars().all()
            ],
        }

    async def _report_failure_stats(self, recent_limit: int):
        total = await self.session.scalar(
            select(func.count()).select_from(ReportTask).where(ReportTask.status == REPORT_FAILED)
        )
        recent_rows = await self.session.execute(
            select(ReportTask)
            .where(ReportTask.status == REPORT_FAILED)
            .order_by(desc(ReportTask.updated_at), desc(ReportTask.id))
            .limit(recent_limit)
        )
        return {
            "total": total or 0,
            "recent": [
                {
                    "id": task.id,
                    "user_id": task.user_id,
                    "record_id": task.record_id,
                    "candidate_id": task.candidate_id,
                    "report_version": task.report_version,
                    "reason": task.error_message,
                    "updated_at": task.updated_at,
                    "created_at": task.created_at,
                }
                for task in recent_rows.scalars().all()
            ],
        }

    async def _visual_failure_stats(self, recent_limit: int):
        total = await self.session.scalar(
            select(func.count()).select_from(VisualGenerationTask).where(VisualGenerationTask.status == VISUAL_FAILED)
        )
        provider_rows = await self.session.execute(
            select(VisualGenerationTask.provider, func.count())
            .where(VisualGenerationTask.status == VISUAL_FAILED)
            .group_by(VisualGenerationTask.provider)
            .order_by(desc(func.count()))
        )
        recent_rows = await self.session.execute(
            select(VisualGenerationTask)
            .where(VisualGenerationTask.status == VISUAL_FAILED)
            .order_by(desc(VisualGenerationTask.updated_at), desc(VisualGenerationTask.id))
            .limit(recent_limit)
        )
        return {
            "total": total or 0,
            "by_provider": [
                {"provider": provider or "unknown", "count": count} for provider, count in provider_rows.all()
            ],
            "recent": [
                {
                    "id": task.id,
                    "user_id": task.user_id,
                    "record_id": task.record_id,
                    "candidate_id": task.candidate_id,
                    "task_type": task.task_type,
                    "provider": task.provider,
                    "reason": task.error_message,
                    "updated_at": task.updated_at,
                    "created_at": task.created_at,
                }
                for task in recent_rows.scalars().all()
            ],
        }
