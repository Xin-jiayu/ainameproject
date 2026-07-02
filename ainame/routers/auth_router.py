import random
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import EmailStr
from redis import Redis
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from core.redisconfig import get_redis_client
from dependencies import get_session
from models.user import User
from repository.user_repo import UserRepository
from schemas.user_schemas import LoginIn, LoginOut, RegisterIn, UserCreateSchema
from services.email_service import EmailService


router = APIRouter(prefix="/auth", tags=["auth"])
authHandler = AuthHandler()


@router.get("/code")
async def get_email_code(
    email: Annotated[EmailStr, Query(...)],
    redis: Redis = Depends(get_redis_client),
):
    code = "".join(random.sample(string.digits * 4, k=4))
    await redis.set(email, code, ex=300)
    await EmailService().enqueue_email(
        subject="【ai起名app】注册验证码",
        recipients=[email],
        body=f"您的验证码是:{code},五分钟内有效，请及时注册账号",
    )
    return {"message": "验证码发送任务已提交"}


@router.post("/register")
async def register(
    userinfo: RegisterIn,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis_client),
):
    user_repository = UserRepository(session=session)
    if await user_repository.email_is_exist(userinfo.email):
        raise HTTPException(status_code=400, detail="该邮箱已经注册，请直接登录")

    email_code = await redis.get(userinfo.email)
    if (not email_code) or (userinfo.code != email_code):
        raise HTTPException(status_code=400, detail="验证码错误或者已经过期")

    user_create_schema = UserCreateSchema(
        email=userinfo.email,
        username=userinfo.username,
        password=userinfo.password,
    )
    await user_repository.create_user(user_create_schema)
    await redis.delete(userinfo.email)
    return {"message": "恭喜您注册成功"}


@router.post(path="/login", response_model=LoginOut)
async def login(userinfo: LoginIn, session: AsyncSession = Depends(get_session)):
    user_repository = UserRepository(session=session)
    user: User | None = await user_repository.get_user_by_email(userinfo.email)
    if not user:
        raise HTTPException(status_code=400, detail="该用户不存在")
    if user.is_frozen:
        raise HTTPException(status_code=403, detail="账号已被冻结")
    if not user.check_password(userinfo.password):
        raise HTTPException(status_code=400, detail="密码输入错误，请核对后输入")
    if session.is_modified(user):
        await session.commit()
        await session.refresh(user)
    tokens = authHandler.encode_login_token(user.id)
    return {
        "user": user,
        "token": tokens["access_token"],
    }
