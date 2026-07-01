import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
# from core.nametools import generate_names
from core.workflow import feedback_names, generate_naming, generate_naming_v2, init_graph
from dependencies import get_session
from repository.name_record_repo import NameRecordRepository
from repository.phase_two_repo import PhaseTwoRepository
from repository.user_repo import UserRepository
from schemas.name_schemas import (
    DeleteRecordOut,
    FeedbackSchema,
    NameIn,
    NameOutSchema,
    NameRecordDetailSchema,
    NameRecordListItemSchema,
    NameSchemaWithThreadOut,
)

auth_handler = AuthHandler()
router = APIRouter(prefix="/names", tags=["names"])


async def consume_quota_or_raise(user_id:int, session:AsyncSession):
    user_repository = UserRepository(session=session)
    quota_change = await user_repository.consume_free_quota(user_id)
    if not quota_change:
        raise HTTPException(status_code=403, detail="免费生成次数已用完，暂时无法新建起名任务")
    return user_repository, quota_change


async def save_usage_record(
    session: AsyncSession,
    user_id: int,
    record_id: int,
    quota_change: dict,
):
    record_repository = NameRecordRepository(session=session)
    await record_repository.create_usage_record(
        user_id=user_id,
        record_id=record_id,
        usage_type="name_generate",
        cost_count=1,
        before_quota=quota_change["before_quota"],
        after_quota=quota_change["after_quota"],
    )


async def save_candidates(session: AsyncSession, record_id: int, result_data: dict, replace: bool = False):
    phase_two_repository = PhaseTwoRepository(session=session)
    if replace:
        return await phase_two_repository.replace_candidates_from_result(record_id, result_data)
    return await phase_two_repository.create_candidates_from_result(record_id, result_data)


# user_id: int = Depends(auth_handler.auth_access_dependency) 用户登录校验，如果没有登录，无法访问
@router.post("/get_names", response_model=NameOutSchema)
async def get_names(name_info: NameIn,
                    user_id: int = Depends(auth_handler.auth_access_dependency),
                    session:AsyncSession=Depends(get_session)):
    user_repository, quota_change = await consume_quota_or_raise(user_id, session)
    try:
        # user_id 是用户创建数据库表的时候用户，当时创用id指定表明，现在查应该用相同的名字才可以
        await init_graph()
        result = await generate_naming(name_info,user_id)
        record_repository = NameRecordRepository(session=session)
        record = await record_repository.create_record(
            user_id=user_id,
            category=name_info.category,
            input_data=name_info.model_dump(),
            result_data=result,
            thread_id=f"legacy-{uuid.uuid4()}",
        )
        await save_candidates(session, record.id, result)
        await save_usage_record(session, user_id, record.id, quota_change)
        return NameOutSchema(names=result["names"])
    except Exception:
        await user_repository.refund_free_quota(user_id)
        raise


@router.post("/generate", response_model=NameSchemaWithThreadOut)
async def generate_names(name_info: NameIn,
                         user_id: int = Depends(auth_handler.auth_access_dependency),
                         session:AsyncSession=Depends(get_session)):
    user_repository, quota_change = await consume_quota_or_raise(user_id, session)
    try:
        # user_id 是用户创建数据库表的时候用户，当时创用id指定表明，现在查应该用相同的名字才可以
        await init_graph()
        result = await generate_naming_v2(name_info,user_id)
        record_repository = NameRecordRepository(session=session)
        record = await record_repository.create_record(
            user_id=user_id,
            category=name_info.category,
            input_data=name_info.model_dump(),
            result_data=result["names"],
            thread_id=result["thread_id"],
        )
        await save_candidates(session, record.id, result["names"])
        await save_usage_record(session, user_id, record.id, quota_change)
        return NameSchemaWithThreadOut(
            thread_id=result["thread_id"],
            names=result["names"]["names"],
            record_id=record.id,
        )
    except Exception:
        await user_repository.refund_free_quota(user_id)
        raise


@router.get("/records", response_model=list[NameRecordListItemSchema])
async def list_records(skip:int = Query(0, ge=0),
                       limit:int = Query(20, ge=1, le=100),
                       user_id: int = Depends(auth_handler.auth_access_dependency),
                       session:AsyncSession=Depends(get_session)):
    record_repository = NameRecordRepository(session=session)
    return await record_repository.list_records(user_id, skip=skip, limit=limit)


@router.get("/records/{record_id}", response_model=NameRecordDetailSchema)
async def get_record(record_id:int,
                     user_id: int = Depends(auth_handler.auth_access_dependency),
                     session:AsyncSession=Depends(get_session)):
    record_repository = NameRecordRepository(session=session)
    record = await record_repository.get_record(user_id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="起名记录不存在")
    feedbacks = await record_repository.list_feedbacks(record.id, user_id)
    return NameRecordDetailSchema(
        id=record.id,
        category=record.category,
        title=record.title,
        input_data=record.input_data,
        result_data=record.result_data,
        thread_id=record.thread_id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        feedbacks=feedbacks,
    )


@router.delete("/records/{record_id}", response_model=DeleteRecordOut)
async def delete_record(record_id:int,
                        user_id: int = Depends(auth_handler.auth_access_dependency),
                        session:AsyncSession=Depends(get_session)):
    record_repository = NameRecordRepository(session=session)
    deleted = await record_repository.delete_record(user_id, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="起名记录不存在")
    return DeleteRecordOut(message="起名记录删除成功")


@router.post("/feedback", response_model=NameSchemaWithThreadOut)
async def feedback(data:FeedbackSchema,
                   user_id: int = Depends(auth_handler.auth_access_dependency),
                   session:AsyncSession=Depends(get_session)):
    record_repository = NameRecordRepository(session=session)
    record = await record_repository.get_record_by_thread_id(user_id, data.thread_id)
    if not record:
        raise HTTPException(status_code=404, detail="起名记录不存在，无法继续优化")
    if not data.category:
        data.category = record.category

    await init_graph()
    result = await feedback_names(data, user_id)
    await record_repository.add_feedback_and_update_record(
        record=record,
        feedback_text=data.feedback,
        result_data=result["names"],
    )
    await save_candidates(session, record.id, result["names"], replace=True)
    return NameSchemaWithThreadOut(
        thread_id=result["thread_id"],
        names=result["names"]["names"],
        record_id=record.id,
    )
