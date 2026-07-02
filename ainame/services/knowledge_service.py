import json
import os
import shutil

import aio_pika
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio.session import AsyncSession

import settings
from repository.knowledge_file_repo import KnowledgeFileRepository


class KnowledgeService:
    """Knowledge file lifecycle and queue submission."""

    QUEUE_NAME = "rag_document_queue"
    UPLOAD_DIR = "./uploads"
    MAX_RETRY_COUNT = 3

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = KnowledgeFileRepository(session=session)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    async def upload_file(self, file: UploadFile, user_id: int):
        file_path = os.path.join(self.UPLOAD_DIR, f"{user_id}_{file.filename}")
        absolute_path = os.path.abspath(file_path)

        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(absolute_path)
        _, ext = os.path.splitext(file.filename)

        knowledge_file = await self.repository.create_file(
            user_id=user_id,
            filename=file.filename,
            file_path=absolute_path,
            file_type=ext.lstrip(".").lower() or None,
            file_size=file_size,
        )
        await self.enqueue_file_task(knowledge_file.id, user_id, absolute_path)
        return knowledge_file

    async def list_files(self, user_id: int, skip: int = 0, limit: int = 20):
        return await self.repository.list_user_files(user_id, skip=skip, limit=limit)

    async def get_file(self, user_id: int, file_id: int):
        knowledge_file = await self.repository.get_user_file(user_id, file_id)
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="知识库文件不存在")
        return knowledge_file

    async def delete_file(self, user_id: int, file_id: int):
        knowledge_file = await self.repository.mark_deleted(user_id, file_id)
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="knowledge file not found")
        return knowledge_file

    async def retry_file(self, user_id: int, file_id: int):
        knowledge_file = await self.repository.get_user_file(user_id, file_id)
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="knowledge file not found")
        if knowledge_file.status == "processing":
            raise HTTPException(status_code=409, detail="knowledge file is processing")
        if knowledge_file.status != "failed":
            raise HTTPException(status_code=400, detail="only failed knowledge files can retry")
        if (knowledge_file.retry_count or 0) >= self.MAX_RETRY_COUNT:
            raise HTTPException(status_code=400, detail="文件处理失败次数已达到上限，请重新上传文件")
        if not os.path.exists(knowledge_file.file_path):
            raise HTTPException(status_code=400, detail="local file does not exist")

        knowledge_file = await self.repository.mark_retrying(user_id, file_id)
        await self.enqueue_file_task(knowledge_file.id, user_id, knowledge_file.file_path)
        return knowledge_file

    async def enqueue_file_task(self, knowledge_file_id: int, user_id: int, file_path: str):
        await self.send_to_queue(
            {
                "knowledge_file_id": knowledge_file_id,
                "user_id": user_id,
                "file_path": file_path,
            }
        )

    async def send_to_queue(self, message_dict: dict):
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.QUEUE_NAME, durable=True)
            message_body = json.dumps(message_dict).encode("utf-8")
            await channel.default_exchange.publish(
                aio_pika.Message(body=message_body),
                routing_key=queue.name,
            )
