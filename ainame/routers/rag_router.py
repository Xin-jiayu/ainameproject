from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from schemas.knowledge_schemas import KnowledgeFileOutSchema
from services.knowledge_service import KnowledgeService


auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["企业知识库"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    knowledge_file = await KnowledgeService(session=session).upload_file(file, user_id)
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
    return await KnowledgeService(session=session).list_files(user_id, skip=skip, limit=limit)


@router.get("/files/{file_id}", response_model=KnowledgeFileOutSchema)
async def get_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await KnowledgeService(session=session).get_file(user_id, file_id)


@router.delete("/files/{file_id}", response_model=KnowledgeFileOutSchema)
async def delete_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await KnowledgeService(session=session).delete_file(user_id, file_id)


@router.post("/files/{file_id}/retry", response_model=KnowledgeFileOutSchema)
async def retry_knowledge_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await KnowledgeService(session=session).retry_file(user_id, file_id)
