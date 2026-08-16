"""Notification service — RabbitMQ integration for async events."""

import json
import logging
from datetime import datetime
from typing import Optional

import aio_pika
from aio_pika import ExchangeType, Message as AioPikaMessage
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractExchange

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


from typing import Optional
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractExchange


class NotificationService:
    """Handles async notifications via RabbitMQ."""

    def __init__(self) -> None:
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchange: Optional[AbstractExchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ and declare exchange. Returns silently if failed."""
        try:
            logger.info("Connecting to RabbitMQ...")
            self._connection = await aio_pika.connect_robust(_settings.rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)

            self._exchange = await self._channel.declare_exchange(
                _settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True,
            )

            logger.info("RabbitMQ connected: exchange=%s", _settings.rabbitmq_exchange)
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ: %s. App will start without it.", e)
            self._connection = None
            self._channel = None
            self._exchange = None


    async def close(self):
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ disconnected")

    async def _ensure_connection(self):
        """Reconnect if connection is closed."""
        if not self._connection or self._connection.is_closed:
            await self.connect()

    async def increment_unread_counters(
        self, conversation_id: str, sender_id: int
    ) -> None:
        """Publish event to increment unread counters for participants."""
        await self._ensure_connection()

        body = json.dumps({
            "type": "increment_unread",
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        assert self._exchange
        await self._exchange.publish(
            AioPikaMessage(body.encode()),
            routing_key="unread.increment",
        )
        logger.debug(
            "Event published: increment_unread conv=%s sender=%s",
            conversation_id,
            sender_id,
        )

    async def notify_new_message(
        self, conversation_id: str, message_id: str
    ) -> None:
        """Publish event for new message (triggers WebSocket push)."""
        await self._ensure_connection()

        body = json.dumps({
            "type": "new_message",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        assert self._exchange
        await self._exchange.publish(
            AioPikaMessage(body.encode()),
            routing_key="message.new",
        )
        logger.debug(
            "Event published: new_message conv=%s msg=%s",
            conversation_id,
            message_id,
        )

    async def notify_messages_read(
        self, conversation_id: str, user_id: int
    ) -> None:
        """Publish event for messages read by a user."""
        await self._ensure_connection()

        body = json.dumps({
            "type": "messages_read",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        assert self._exchange
        await self._exchange.publish(
            AioPikaMessage(body.encode()),
            routing_key="message.read",
        )
        logger.debug(
            "Event published: messages_read conv=%s user=%s",
            conversation_id,
            user_id,
        )

    async def archive_messages_task(self) -> None:
        """Publish event to trigger message archival."""
        await self._ensure_connection()

        body = json.dumps({
            "type": "archive_messages",
            "timestamp": datetime.utcnow().isoformat(),
        })
        assert self._exchange
        await self._exchange.publish(
            AioPikaMessage(body.encode()),
            routing_key="archive.messages",
        )
        logger.info("Event published: archive_messages")

    async def send_push_notification(
        self, user_id: int, message: str
    ) -> None:
        """Publish event for push notification."""
        await self._ensure_connection()

        body = json.dumps({
            "type": "push_notification",
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })
        assert self._exchange
        await self._exchange.publish(
            AioPikaMessage(body.encode()),
            routing_key=f"push.user.{user_id}",
        )
        logger.debug("Event published: push_notification user=%s", user_id)
