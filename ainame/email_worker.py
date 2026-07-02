import asyncio
import json
import sys

import aio_pika

import settings
from services.email_service import EmailService


RABBITMQ_URL = settings.RABBITMQ_URL
QUEUE_NAME = EmailService.QUEUE_NAME


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        payload = json.loads(message.body.decode("utf-8"))
        recipients = payload.get("recipients", [])
        print(f"[EmailWorker] sending email to {recipients}")
        await EmailService().send_from_payload(payload)
        print(f"[EmailWorker] email sent to {recipients}")


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=5)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print(f"[*] Email worker started, listening on '{QUEUE_NAME}'. Press CTRL+C to exit.")
    await queue.consume(process_message)
    await asyncio.Future()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
