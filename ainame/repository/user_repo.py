from datetime import datetime, timedelta

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.user import EmailCode, User
from schemas.user_schemas import UserCreateSchema


# 与email表交互的对象
class EmailCodeRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    # 把一条emailcode数据插入到数据库
    async def create_email_code(self, email:str, code:str):
        async with self.session.begin():
            # 准备与email_code表对应的一个对象
            email_code = EmailCode(email=email,code=code)
            self.session.add(email_code)
        return email_code

    # 这是对验证码的校验函数
    async def check_email_code(self, email:str,code:str):
        async with self.session.begin():
            # select * from emailcode where email="" and code=""
            email_code=await self.session.scalar(select(EmailCode).filter(EmailCode.email==email,EmailCode.code==code))
            # 数据库如果没有email_code这个类，说明没有发送验证码
            if not email_code:
                return False
            # 如果过期了，超过5分钟，验证码失效
            if(datetime.now() - email_code.created_time) >= timedelta(minutes=5):
                return False
            return True


# 与user表交互的对象
class UserRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    # 我判断用户传过来的邮箱是否已经被他人注册过
    async def get_user_by_email(self, email:str):
        result = await self.session.execute(select(User).where(User.email==email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id:int):
        result = await self.session.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()

    # 插入一条数据
    async def create_user(self, user:UserCreateSchema):
        async with self.session.begin():
            # user.model_dump() 把对象属性数据变成字典
            user=User(**user.model_dump())
            self.session.add(user)
            return user

    # 我判断用户传过来的邮箱是否已经被他人注册过
    async def email_is_exist(self,email:str):
        async with self.session.begin():
            stmt=select(exists().where(User.email==email))
            return await self.session.scalar(stmt)

    async def email_is_used_by_other(self, email:str, user_id:int):
        stmt=select(exists().where(User.email == email, User.id != int(user_id)))
        return await self.session.scalar(stmt)

    async def list_users(self, page:int = 1, page_size:int = 20, keyword:str | None = None):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        conditions = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            conditions.append(or_(User.email.like(like_keyword), User.username.like(like_keyword)))

        where_clause = conditions[0] if conditions else None
        total_stmt = select(func.count()).select_from(User)
        list_stmt = select(User).order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
        if where_clause is not None:
            total_stmt = total_stmt.where(where_clause)
            list_stmt = list_stmt.where(where_clause)

        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt)
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    async def update_user(self, user_id:int, data:dict):
        async with self.session.begin():
            user = await self.session.scalar(select(User).where(User.id == int(user_id)).with_for_update())
            if not user:
                return None
            for key, value in data.items():
                setattr(user, key, value)
            return user

    async def set_user_frozen(self, user_id:int, is_frozen:bool):
        return await self.update_user(user_id, {"is_frozen": is_frozen})

    async def reset_user_password(self, user_id:int, password:str):
        async with self.session.begin():
            user = await self.session.scalar(select(User).where(User.id == int(user_id)).with_for_update())
            if not user:
                return None
            user.password = password
            return user

    async def delete_user(self, user_id:int):
        async with self.session.begin():
            user = await self.session.scalar(select(User).where(User.id == int(user_id)).with_for_update())
            if not user:
                return None
            await self.session.delete(user)
            return user

    async def consume_free_quota(self, user_id:int):
        async with self.session.begin():
            stmt = select(User).where(User.id == int(user_id)).with_for_update()
            user = await self.session.scalar(stmt)
            if not user or user.free_quota <= 0:
                return None
            before_quota = user.free_quota
            user.free_quota -= 1
            return {
                "before_quota": before_quota,
                "after_quota": user.free_quota,
            }

    async def refund_free_quota(self, user_id:int):
        async with self.session.begin():
            stmt = select(User).where(User.id == int(user_id)).with_for_update()
            user = await self.session.scalar(stmt)
            if user:
                user.free_quota += 1
