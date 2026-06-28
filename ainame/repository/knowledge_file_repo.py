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
            .where(KnowledgeFile.user_id == int(user_id))
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
        knowledge_file.status = status
        knowledge_file.error_message = error_message
        knowledge_file.updated_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(knowledge_file)
        return knowledge_file