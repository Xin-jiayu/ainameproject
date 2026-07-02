from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

from repository.user_repo import UserRepository


class UserService:
    """User account, quota, and entitlement business operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session=session)

    async def consume_quota_or_raise(self, user_id: int):
        quota_change = await self.user_repository.consume_free_quota(user_id)
        if not quota_change:
            raise HTTPException(status_code=403, detail="免费生成次数已用完，暂时无法新建起名任务")
        return quota_change

    async def refund_free_quota(self, user_id: int):
        await self.user_repository.refund_free_quota(user_id)

    async def get_entitlements(self, user_id: int):
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {
            "user_id": user.id,
            "free_quota": user.free_quota,
            "is_frozen": user.is_frozen,
            "is_admin": user.is_admin,
        }

    async def ensure_active_user(self, user_id: int):
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        if user.is_frozen:
            raise HTTPException(status_code=403, detail="账号已被冻结")
        return user

    async def list_users(self, page: int = 1, page_size: int = 20, keyword: str | None = None):
        return await self.user_repository.list_users(page=page, page_size=page_size, keyword=keyword)

    async def update_user(self, user_id: int, data: dict, current_admin_id: int):
        if not data:
            raise HTTPException(status_code=400, detail="没有需要修改的字段")
        if user_id == current_admin_id and data.get("is_frozen") is True:
            raise HTTPException(status_code=400, detail="不能冻结当前管理员账号")
        if user_id == current_admin_id and data.get("is_admin") is False:
            raise HTTPException(status_code=400, detail="不能取消当前管理员账号的管理员权限")
        if "email" in data and await self.user_repository.email_is_used_by_other(data["email"], user_id):
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")

        user = await self.user_repository.update_user(user_id, data)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user

    async def set_user_frozen(self, user_id: int, is_frozen: bool, current_admin_id: int):
        if user_id == current_admin_id and is_frozen:
            raise HTTPException(status_code=400, detail="不能冻结当前管理员账号")
        user = await self.user_repository.set_user_frozen(user_id, is_frozen)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user

    async def reset_user_password(self, user_id: int, password: str):
        user = await self.user_repository.reset_user_password(user_id, password)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user

    async def delete_user(self, user_id: int, current_admin_id: int):
        if user_id == current_admin_id:
            raise HTTPException(status_code=400, detail="不能删除当前管理员账号")
        user = await self.user_repository.delete_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
