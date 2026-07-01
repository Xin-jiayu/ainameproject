from sqlalchemy import Integer, String , DateTime
from sqlalchemy.orm import Mapped, mapped_column
from . import Base
from datetime import datetime

def get_password_hash():
    from pwdlib import PasswordHash
    return PasswordHash.recommended()

class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100),unique=True)
    username:Mapped[str] = mapped_column(String(100))
    free_quota:Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    # 数据库中存储的是加密后的密码，不是明文  123456 dsfgsdgtuaseffgasgsd
    _password:Mapped[str] = mapped_column(String(200))

    # 1.校验数据：密码是否正确
    #  *args 能够接收任意多个不带名字的参数  列表
    #  **kwargs 能接受任意多个带名字的参数  字典
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        password = kwargs.pop("password",None)
        if password:
            # 增加了一个变量 password  设置password，会自动调用@password.setter
            self.password=password
    #凡是获取passwor的时候，调用这个函数
    @property
    def password(self):
        return self._password
    # 设置password  默认调用,凡是给password赋值，都会调用
    @password.setter
    def password(self,password):
        self._password=get_password_hash().hash(password)
    # 校验密码  你登录淘宝，随便输入一个秘密，它会报告，密码错误。
    def check_password(self,password):
        try:
            return get_password_hash().verify(password,self._password)
        except Exception:
            if password == self._password:
                self.password = password
                return True
            return False

class EmailCode(Base):
    __tablename__ = "email_code"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100))
    code:Mapped[str] = mapped_column(String(100))
    #发送的验证码有时效
    created_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now())

