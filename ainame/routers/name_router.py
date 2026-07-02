from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from schemas.name_schemas import (
    DeleteRecordOut,
    FeedbackSchema,
    NameIn,
    NameOutSchema,
    NameRecordDetailSchema,
    NameRecordListItemSchema,
    NameSchemaWithThreadOut,
    NameTaskOut,
    NameTaskSubmitOut,
)
from services.name_service import NameService


auth_handler = AuthHandler()
router = APIRouter(prefix="/names", tags=["names"])


@router.post("/get_names", response_model=NameOutSchema)
async def get_names(
    name_info: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).generate_legacy_names(name_info, user_id)


@router.post("/generate", response_model=NameSchemaWithThreadOut)
async def generate_names(
    name_info: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).generate_names(name_info, user_id)


@router.post("/tasks", response_model=NameTaskSubmitOut)
async def submit_name_task(
    name_info: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).submit_generation_task(name_info, user_id)


@router.get("/tasks/{task_id}", response_model=NameTaskOut)
async def get_name_task(
    task_id: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).get_generation_task(user_id, task_id)


@router.get("/records", response_model=list[NameRecordListItemSchema])
async def list_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).list_records(user_id, skip=skip, limit=limit)


@router.get("/records/{record_id}", response_model=NameRecordDetailSchema)
async def get_record(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).get_record_detail(user_id, record_id)


@router.delete("/records/{record_id}", response_model=DeleteRecordOut)
async def delete_record(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    await NameService(session=session).delete_record(user_id, record_id)
    return DeleteRecordOut(message="起名记录删除成功")


@router.post("/feedback", response_model=NameSchemaWithThreadOut)
async def feedback(
    data: FeedbackSchema,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameService(session=session).feedback(data, user_id)
