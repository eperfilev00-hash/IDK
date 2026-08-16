"""Message repository for MongoDB using Beanie."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from beanie import PydanticObjectId

from app.models.chat_models import Message, MessageStatus

logger = logging.getLogger(__name__)


class MessageRepository:
    """Repository for messages in MongoDB."""

    async def get_messages_by_cursor(
        self,
        conversation_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
        after_id: Optional[str] = None,
    ) -> List[Message]:
        """Cursor-based pagination for messages."""
        query = Message.find(
            {"conversation_id": conversation_id, "is_deleted": False}
        ).sort("-created_at")

        if before_id:
            before_msg = await Message.get(PydanticObjectId(before_id))  # type: ignore[misc]
            if before_msg:
                query = query.find({"created_at": {"$lt": before_msg.created_at}})
        elif after_id:
            after_msg = await Message.get(PydanticObjectId(after_id))  # type: ignore[misc]
            if after_msg:
                query = query.find({"created_at": {"$gt": after_msg.created_at}})

        messages = await (
            query.limit(limit).to_list()
        )
        return list(reversed(messages))

    async def create_message(
        self,
        conversation_id: str,
        sender_id: int,
        content: str,
        content_type: str = "text",
        reply_to_id: Optional[str] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            content_type=content_type,
            reply_to_id=reply_to_id,
        )
        await message.insert()  # type: ignore[misc]
        return message

    async def update_message_status(
        self, message_id: str, status: MessageStatus
    ) -> None:
        """Update message status."""
        message = await Message.get(PydanticObjectId(message_id))  # type: ignore[misc]
        if message:
            message.status = status
            await message.save_changes()  # type: ignore[misc]

    async def edit_message(
        self, message_id: str, new_content: str
    ) -> Optional[Message]:
        """Edit a message's content."""
        message = await Message.get(PydanticObjectId(message_id))  # type: ignore[misc]
        if message and not message.is_deleted:
            message.content = new_content
            message.edited_at = datetime.utcnow()
            await message.save_changes()  # type: ignore[misc]
        return message

    async def soft_delete_message(
        self, message_id: str, user_id: int
    ) -> bool:
        """Soft-delete a message (only by its sender)."""
        message = await Message.get(PydanticObjectId(message_id))  # type: ignore[misc]
        if message and message.sender_id == user_id and not message.is_deleted:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            await message.save_changes()  # type: ignore[misc]
            return True
        return False

    async def get_messages_count_in_window(
        self, sender_id: int, window_seconds: int
    ) -> int:
        """Count messages sent by a user within a time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        query = Message.find(
            {"sender_id": sender_id, "created_at": {"$gte": cutoff}, "is_deleted": False}
        )
        return await query.count()

    async def archive_old_messages(
        self, months: int = 6
    ) -> int:
        """Mark messages older than N months as deleted (soft-archive)."""
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        query = Message.find(
            {"created_at": {"$lt": cutoff}, "is_deleted": False}
        )
        messages = await query.to_list()
        for msg in messages:
            msg.is_deleted = True
            await msg.save_changes()  # type: ignore[misc]
        return len(messages)
