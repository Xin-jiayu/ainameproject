from core.auth import AuthHandler
from core.mailtools import create_mail_instance
from fastapi import Depends, HTTPException
from fastapi_mail import FastMail
from repository.user_repo import UserRepository
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

async def get_email():
    return create_mail_instance()


from models import AsyncSessionFactory

async def get_session():
    session = AsyncSessionFactory()
    try:
        # yield 借出去session，意味着，如果用完，再换回来
        yield session
    finally:
        await session.close()


auth_handler = AuthHandler()


async def get_current_user(
    user_id: str = Depends(auth_handler.auth_access_dependency),
    session=Depends(get_session),
):
    user = await UserRepository(session=session).get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.is_frozen:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="账号已被冻结")
    return user


async def get_admin_user(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user
