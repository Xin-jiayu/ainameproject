from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from dependencies import get_admin_user, get_session
from repository.admin_operation_log_repo import AdminOperationLogRepository
from schemas.user_schemas import (
    AdminUserFreezeIn,
    AdminUserListOut,
    AdminUserResetPasswordIn,
    AdminUserSchema,
    AdminUserUpdateIn,
)
from services.user_service import UserService


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


async def log_admin_action(
    session: AsyncSession,
    admin_user,
    action: str,
    resource_type: str,
    resource_id: int | str | None = None,
    details: dict | None = None,
):
    await AdminOperationLogRepository(session=session).create_log(
        admin_user_id=admin_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )


@router.get("", response_model=AdminUserListOut)
async def list_users(
    keyword: str | None = Query(None, description="按邮箱或用户名搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await UserService(session=session).list_users(page=page, page_size=page_size, keyword=keyword)


@router.patch("/{user_id}", response_model=AdminUserSchema)
async def update_user(
    user_id: int,
    userinfo: AdminUserUpdateIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    data = userinfo.model_dump(exclude_unset=True)
    user = await UserService(session=session).update_user(user_id, data, current_admin_id=admin_user.id)
    await log_admin_action(
        session,
        admin_user,
        action="update_user",
        resource_type="user",
        resource_id=user_id,
        details={"fields": sorted(data.keys())},
    )
    return user


@router.post("/{user_id}/freeze", response_model=AdminUserSchema)
async def freeze_user(
    user_id: int,
    freeze_info: AdminUserFreezeIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    user = await UserService(session=session).set_user_frozen(
        user_id,
        freeze_info.is_frozen,
        current_admin_id=admin_user.id,
    )
    await log_admin_action(
        session,
        admin_user,
        action="freeze_user" if freeze_info.is_frozen else "unfreeze_user",
        resource_type="user",
        resource_id=user_id,
        details={"is_frozen": freeze_info.is_frozen},
    )
    return user


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_info: AdminUserResetPasswordIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    await UserService(session=session).reset_user_password(user_id, password_info.password)
    await log_admin_action(
        session,
        admin_user,
        action="reset_user_password",
        resource_type="user",
        resource_id=user_id,
        details=None,
    )
    return {"message": "密码已重置"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    user = await UserService(session=session).delete_user(user_id, current_admin_id=admin_user.id)
    await log_admin_action(
        session,
        admin_user,
        action="delete_user",
        resource_type="user",
        resource_id=user_id,
        details={"email": user.email},
    )
    return {"message": "用户已删除"}
