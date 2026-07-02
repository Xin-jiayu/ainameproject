from pydantic import BaseModel, EmailStr, Field, model_validator, ValidationError
from typing import Annotated

#接收用户传过来的数据的一个对象
RawPasswordStr = Annotated[str,Field(...,min_length=6,max_length=50)]
RawUsernamedStr = Annotated[str,Field(...,min_length=4,max_length=50)]
class RegisterIn(BaseModel):
    email: EmailStr
    username: Annotated[str,Field(...,min_length=4,max_length=50)]
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    code:Annotated[str,Field(...,min_length=4,max_length=4)]
    #完成确认密码的校验
    @model_validator(mode="after")
    def password_is_valid(self,password:str) -> bool:
        password = self.password.strip()
        confirm_password = self.confirm_password.strip()
        if password != confirm_password:
            raise ValidationError("Passwords don't match")
        return self

#存入数据库的是少数字段
class UserCreateSchema(BaseModel):
    email: EmailStr
    username: RawUsernamedStr
    password: RawPasswordStr


# 开发对象，接收用户登录信息
class LoginIn(BaseModel):
    email:EmailStr
    password:RawPasswordStr

class UserSchema(BaseModel):
    id:Annotated[int,Field(...)]
    username: RawUsernamedStr
    email: EmailStr
    free_quota: Annotated[int,Field(...)]
    is_admin: Annotated[bool,Field(...)]
    is_frozen: Annotated[bool,Field(...)]


class AdminUserSchema(UserSchema):
    pass


class AdminUserListOut(BaseModel):
    items: list[AdminUserSchema]
    total: int
    page: int
    page_size: int


class AdminUserUpdateIn(BaseModel):
    email: EmailStr | None = None
    username: Annotated[str,Field(min_length=4,max_length=50)] | None = None
    free_quota: Annotated[int,Field(ge=0)] | None = None
    is_admin: bool | None = None
    is_frozen: bool | None = None


class AdminUserFreezeIn(BaseModel):
    is_frozen: bool


class AdminUserResetPasswordIn(BaseModel):
    password: RawPasswordStr

from models.user import User
class LoginOut(BaseModel):
    user:UserSchema
    token: str

