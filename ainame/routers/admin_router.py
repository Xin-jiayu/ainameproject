from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from dependencies import get_admin_user, get_session
from schemas.user_schemas import (
    AdminUserFreezeIn,
    AdminUserListOut,
    AdminUserResetPasswordIn,
    AdminUserSchema,
    AdminUserUpdateIn,
)
from services.user_service import UserService


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


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
    return await UserService(session=session).update_user(user_id, data, current_admin_id=admin_user.id)


@router.post("/{user_id}/freeze", response_model=AdminUserSchema)
async def freeze_user(
    user_id: int,
    freeze_info: AdminUserFreezeIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await UserService(session=session).set_user_frozen(
        user_id,
        freeze_info.is_frozen,
        current_admin_id=admin_user.id,
    )


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_info: AdminUserResetPasswordIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    await UserService(session=session).reset_user_password(user_id, password_info.password)
    return {"message": "密码已重置"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    await UserService(session=session).delete_user(user_id, current_admin_id=admin_user.id)
    return {"message": "用户已删除"}
