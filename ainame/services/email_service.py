import json

import aio_pika
from fastapi_mail import MessageSchema, MessageType

import settings
from core.mailtools import create_mail_instance


class EmailService:
    """Email delivery through RabbitMQ."""

    QUEUE_NAME = "email_queue"

    async def enqueue_email(self, subject: str, recipients: list[str], body: str):
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.QUEUE_NAME, durable=True)
            payload = {
                "subject": subject,
                "recipients": recipients,
                "body": body,
                "subtype": "plain",
            }
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(payload).encode("utf-8")),
                routing_key=queue.name,
            )

    async def send_email(self, subject: str, recipients: list[str], body: str):
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.plain,
        )
        await create_mail_instance().send_message(message)

    async def send_from_payload(self, payload: dict):
        await self.send_email(
            subject=payload["subject"],
            recipients=payload["recipients"],
            body=payload["body"],
        )
