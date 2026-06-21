import redis.asyncio as redis
from typing import  AsyncGenerator

url="redis://127.0.0.1:6379"
# 创建一个全局的 Redis 连接池
# decode_responses=True 会自动将拿到的 bytes 解码为 str
redis_client = redis.from_url(url,encoding="utf-8",decode_responses=True)
# 定义一个依赖函数，供 FastAPI 路由使用
async def get_redis_client() -> AsyncGenerator[redis.Redis,None]:
    yield redis_client