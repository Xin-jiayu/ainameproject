from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.observability import request_logging_middleware, setup_logging
from routers.admin_router import router as admin_router
from routers.auth_router import router as auth_router
from routers.commerce_router import router as commerce_router
from routers.name_router import router as name_router
from routers.ops_router import router as ops_router
from routers.phase_two_router import router as phase_two_router
from routers.rag_router import router as rag_router
from routers.user_router import router as user_router
from services.email_service import EmailService


setup_logging()
app = FastAPI()
app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(commerce_router)
app.include_router(name_router)
app.include_router(rag_router)
app.include_router(ops_router)
app.include_router(phase_two_router)
app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/mail/test")
async def mail_test(email: str):
    await EmailService().enqueue_email(
        subject="ainame测试邮件",
        recipients=[email],
        body=f"Hello {email}",
    )
    return {"message": "邮件发送任务已提交"}
