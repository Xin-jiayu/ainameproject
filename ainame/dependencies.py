from core.mailtools import create_mail_instance
from fastapi_mail import FastMail

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
