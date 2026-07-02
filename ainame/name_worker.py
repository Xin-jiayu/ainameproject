import asyncio
import json
import sys

import aio_pika

import settings
from models import AsyncSessionFactory
from services.name_service import NameService


RABBITMQ_URL = settings.RABBITMQ_URL
QUEUE_NAME = NameService.QUEUE_NAME


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        task_data = json.loads(message.body.decode("utf-8"))
        task_id = task_data.get("task_id")
        if not task_id:
            print("[NameWorker] missing task_id, skipping message")
            return

        session = AsyncSessionFactory()
        try:
            print(f"[NameWorker] start task {task_id}")
            task = await NameService(session=session).run_generation_task(task_id)
            if task:
                print(f"[NameWorker] task {task_id} finished with status={task.status}")
            else:
                print(f"[NameWorker] task {task_id} not found")
        finally:
            await session.close()


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print(f"[*] Name generation worker started, listening on '{QUEUE_NAME}'. Press CTRL+C to exit.")
    await queue.consume(process_message)
    await asyncio.Future()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
