from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import AdminOperationLog


class AdminOperationLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        admin_user_id: int,
        action: str,
        resource_type: str,
        resource_id: str | int | None = None,
        details: dict | None = None,
    ):
        log = AdminOperationLog(
            admin_user_id=int(admin_user_id),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        admin_user_id: int | None = None,
        resource_type: str | None = None,
    ):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(AdminOperationLog)
        list_stmt = select(AdminOperationLog).order_by(desc(AdminOperationLog.created_at), desc(AdminOperationLog.id))
        if admin_user_id is not None:
            total_stmt = total_stmt.where(AdminOperationLog.admin_user_id == int(admin_user_id))
            list_stmt = list_stmt.where(AdminOperationLog.admin_user_id == int(admin_user_id))
        if resource_type:
            total_stmt = total_stmt.where(AdminOperationLog.resource_type == resource_type)
            list_stmt = list_stmt.where(AdminOperationLog.resource_type == resource_type)
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }
