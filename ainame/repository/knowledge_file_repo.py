from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import KnowledgeFile


class KnowledgeFileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_file(
        self,
        user_id: int,
        filename: str,
        file_path: str,
        file_type: str | None = None,
        file_size: int | None = None,
    ):
        knowledge_file = KnowledgeFile(
            user_id=int(user_id),
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status="pending",
        )
        self.session.add(knowledge_file)
        await self.session.commit()
        await self.session.refresh(knowledge_file)
        return knowledge_file

    async def list_user_files(self, user_id: int, skip: int = 0, limit: int = 20):
        stmt = (
            select(KnowledgeFile)
            .where(
                KnowledgeFile.user_id == int(user_id),
                KnowledgeFile.is_deleted.is_(False),
            )
            .order_by(desc(KnowledgeFile.updated_at), desc(KnowledgeFile.id))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_file(self, user_id: int, knowledge_file_id: int):
        stmt = select(KnowledgeFile).where(
            KnowledgeFile.id == int(knowledge_file_id),
            KnowledgeFile.user_id == int(user_id),
            KnowledgeFile.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_file(self, knowledge_file_id: int):
        stmt = select(KnowledgeFile).where(KnowledgeFile.id == int(knowledge_file_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        knowledge_file_id: int,
        status: str,
        error_message: str | None = None,
    ):
        knowledge_file = await self.get_file(knowledge_file_id)
        if not knowledge_file:
            return None
        if knowledge_file.is_deleted:
            return knowledge_file
        knowledge_file.status = status
        knowledge_file.error_message = error_message
        if status == "completed":
            knowledge_file.processed_at = datetime.now()
        if status in {"pending", "processing"}:
            knowledge_file.processed_at = None
        knowledge_file.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(knowledge_file)
        return knowledge_file

    async def mark_deleted(self, user_id: int, knowledge_file_id: int):
        knowledge_file = await self.get_user_file(user_id, knowledge_file_id)
        if not knowledge_file:
            return None
        knowledge_file.is_deleted = True
        knowledge_file.status = "deleted"
        knowledge_file.deleted_at = datetime.now()
        knowledge_file.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(knowledge_file)
        return knowledge_file

    async def mark_retrying(self, user_id: int, knowledge_file_id: int):
        knowledge_file = await self.get_user_file(user_id, knowledge_file_id)
        if not knowledge_file:
            return None
        knowledge_file.status = "pending"
        knowledge_file.error_message = None
        knowledge_file.retry_count = (knowledge_file.retry_count or 0) + 1
        knowledge_file.processed_at = None
        knowledge_file.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(knowledge_file)
        return knowledge_file
