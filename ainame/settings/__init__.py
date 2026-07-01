import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required. Set it in environment variables or ainame/.env")
    return value


def get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DB_URI = get_required_env("DB_URI")

MAIL_USERNAME = get_required_env("MAIL_USERNAME")
MAIL_PASSWORD = get_required_env("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = get_bool_env("MAIL_STARTTLS", True)
MAIL_SSL_TLS = get_bool_env("MAIL_SSL_TLS", False)

JWT_SECRET_KEY = get_required_env("JWT_SECRET_KEY")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", "1")))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30")))

RABBITMQ_URL = get_required_env("RABBITMQ_URL")
REDIS_URL = get_required_env("REDIS_URL")
DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")
POSTGRES_MEMORY_DB_URI = get_required_env("POSTGRES_MEMORY_DB_URI")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REQUEST_SLOW_MS = int(os.getenv("REQUEST_SLOW_MS", "1000"))
