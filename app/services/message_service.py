"""Message service — business logic for sending, fetching and editing messages."""

import json
import logging
from typing import List, Optional

from app.config import get_settings
from app.repository.chat_repo import ChatRepository
from app.services.cache import cache_service
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
_settings = get_settings()


class MessageService:
    """Service for message operations."""

    def __init__(self, repo: ChatRepository):
        self.repo = repo
        self.notifications = NotificationService()

    # ======================== SEND ========================

    async def send_message(
        self,
        sender_id: int,
        conversation_id: str,
        content: str,
        content_type: str = "text",
        reply_to_id: Optional[str] = None,
    ) -> dict:
        """Send a new message. DB write + async notifications."""
        # Rate limiting check
        count = await self.repo.messages.get_messages_count_in_window(
            sender_id, _settings.rate_limit_window
        )
        if count >= _settings.rate_limit_messages:
            raise Exception(
                f"Rate limit exceeded: {_settings.rate_limit_messages} messages per {_settings.rate_limit_window}s"
            )

        # Create message and body
        message = await self.repo.messages.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            content_type=content_type,
            reply_to_id=reply_to_id,
        )

        # Update last message reference in conversation
        await self.repo.conversations.update_last_message(
            conversation_id, str(message.id), message.created_at
        )

        # Async: increment unread counters for other participants
        await self.notifications.increment_unread_counters(
            conversation_id, sender_id
        )

        # Async: notify via WebSocket
        await self.notifications.notify_new_message(
            conversation_id, str(message.id)
        )

        # Invalidate conversations cache
        await cache_service.delete_pattern("conversations_list:*")

        return self._to_dict(message)

    # ======================== FETCH ========================

    async def get_messages(
        self,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        before_id: Optional[str] = None,
        after_id: Optional[str] = None,
    ) -> List[dict]:
        """Get messages with cursor-based pagination and caching."""
        cache_key = f"chat:messages:{conversation_id}:{before_id or 'all'}:{limit}"
        cached = await cache_service.get(cache_key)
        if cached and not before_id:
            logger.debug("Messages cache hit: %s", cache_key)
            return json.loads(cached)

        messages = await self.repo.messages.get_messages_by_cursor(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
            after_id=after_id,
        )

        result = [self._to_dict(m) for m in messages]

        # Only cache when no cursor (initial load)
        if not before_id:
            await cache_service.set(
                cache_key,
                json.dumps(result, default=str, ensure_ascii=False),
                ttl=_settings.CONVERSATION_MESSAGES_TTL,
            )

        return result

    # ======================== ACTIONS ========================

    async def mark_as_read(
        self, conversation_id: str, user_id: int
    ) -> int:
        """Mark all messages in a conversation as read."""
        count = await self.repo.read_receipts.bulk_mark_read(
            conversation_id, user_id
        )

        # Async: notify senders
        await self.notifications.notify_messages_read(
            conversation_id, user_id
        )

        # Invalidate cache
        await cache_service.delete_pattern(f"chat:messages:{conversation_id}:*")

        return count

    async def edit_message(
        self, message_id: str, user_id: int, new_content: str
    ) -> Optional[dict]:
        """Edit an existing message."""
        message = await self.repo.messages.edit_message(
            message_id, new_content
        )
        if message:
            return self._to_dict(message)
        return None

    async def delete_message(
        self, message_id: str, user_id: int
    ) -> bool:
        """Soft-delete a message."""
        result = await self.repo.messages.soft_delete_message(
            message_id, user_id
        )
        if result:
            await cache_service.delete_pattern("conversations_list:*")
        return result

    # ======================== HELPERS ========================

    def _to_dict(self, message) -> dict:
        """Convert Message model to dict."""
        return {
            "id": str(message.id),
            "sender_id": message.sender_id,
            "sender": None,  # User info fetched separately if needed
            "body": message.content,
            "body_type": message.content_type,
            "reply_to_id": message.reply_to_id,
            "status": message.status.value if hasattr(message.status, "value") else message.status,
            "created_at": message.created_at.isoformat(),
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "is_deleted": message.is_deleted,
            "attachments": message.attachments,
        }
