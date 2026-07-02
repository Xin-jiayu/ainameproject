import json
import os
import shutil

import settings

import aio_pika
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from repository.knowledge_file_repo import KnowledgeFileRepository
from schemas.knowledge_schemas import KnowledgeFileOutSchema

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["企业知识库"])

# 启动项目所在的根文件的路径，在我们项目中是ai397下main创建一个文件夹uploads
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# RabbitMQ 连接配置 协议://用户名:密码@主机地址:端口号
RABBITMQ_URL = settings.RABBITMQ_URL
QUEUE_NAME = "rag_document_queue"
MAX_KNOWLEDGE_FILE_RETRY_COUNT = 3


def has_reached_retry_limit(knowledge_file) -> bool:
    return (knowledge_file.retry_count or 0) >= MAX_KNOWLEDGE_FILE_RETRY_COUNT


async def send_to_queue(message_dict: dict):
    """异步将任务发送到 RabbitMQ 队列"""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # declare_queue，如果没有，创建。声明队列：durable=True 开启持久化，服务器重启任务 不丢
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        # 将任务字典转为 JSON 字节流发送
        message_body = json.dumps(message_dict).encode("utf-8")
        # 调用默认交换机，把封装好的消息发布出去
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            # 路由键只要和队列名字一模一样
            routing_key=queue.name,
        )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """
    用户上传专属参考文件（TXT/PDF）
    """
    # 第一步：完成文件在服务器的保存
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")

    # 注意这里转换成绝对路径
    absolute_path = os.path.abspath(file_path)

    with open(absolute_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(absolute_path)
    _, ext = os.path.splitext(file.filename)

    knowledge_file_repository = KnowledgeFileRepository(session=session)
    knowledge_file = await knowledge_file_repository.create_file(
        user_id=user_id,
        filename=file.filename,
        file_path=absolute_path,
        file_type=ext.lstrip(".").lower() or None,
        file_size=file_size,
    )

    # 第二步：把已经上传的文件，插入到知识库的数据库中
    # 把任务添加到消息队列
    task_message = {
        "knowledge_file_id": knowledge_file.id,
        "user_id": user_id,
        "file_path": absolute_path,
    }
    await send_to_queue(task_message)

    return {
        "result": "success",
        "knowledge_file_id": knowledge_file.id,
        "status": knowledge_file.status,
        "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。",
    }


@router.get("/files", response_model=list[KnowledgeFileOutSchema])
async def list_knowledge_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = KnowledgeFileRepository(session=session)
    return await repository.list_user_files(user_id, skip=skip, limit=limit)


@router.get("/files/{file_id}", response_model=KnowledgeFileOutSchema)
async def get_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = KnowledgeFileRepository(session=session)
    knowledge_file = await repository.get_user_file(user_id, file_id)
    if not knowledge_file:
        raise HTTPException(status_code=404, detail="知识库文件不存在")
    return knowledge_file


@router.delete("/files/{file_id}", response_model=KnowledgeFileOutSchema)
async def delete_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = KnowledgeFileRepository(session=session)
    knowledge_file = await repository.mark_deleted(user_id, file_id)
    if not knowledge_file:
        raise HTTPException(status_code=404, detail="knowledge file not found")
    return knowledge_file


@router.post("/files/{file_id}/retry", response_model=KnowledgeFileOutSchema)
async def retry_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = KnowledgeFileRepository(session=session)
    knowledge_file = await repository.get_user_file(user_id, file_id)
    if not knowledge_file:
        raise HTTPException(status_code=404, detail="knowledge file not found")
    if knowledge_file.status == "processing":
        raise HTTPException(status_code=409, detail="knowledge file is processing")
    if knowledge_file.status != "failed":
        raise HTTPException(status_code=400, detail="only failed knowledge files can retry")
    if has_reached_retry_limit(knowledge_file):
        raise HTTPException(status_code=400, detail="文件处理失败次数已达到上限，请重新上传文件")
    if not os.path.exists(knowledge_file.file_path):
        raise HTTPException(status_code=400, detail="local file does not exist")

    knowledge_file = await repository.mark_retrying(user_id, file_id)
    task_message = {
        "knowledge_file_id": knowledge_file.id,
        "user_id": user_id,
        "file_path": knowledge_file.file_path,
    }
    await send_to_queue(task_message)
    return knowledge_file
