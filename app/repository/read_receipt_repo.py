"""Read receipt repository for MongoDB using Beanie."""

import logging
from typing import List

from beanie import PydanticObjectId

from app.models.chat_models import Message, ReadReceipt

logger = logging.getLogger(__name__)


class ReadReceiptRepository:
    """Repository for read receipts in MongoDB."""

    async def create_read_receipt(
        self, message_id: str, user_id: int
    ) -> ReadReceipt:
        """Create a read receipt for a message."""
        receipt = ReadReceipt(
            message_id=message_id,
            user_id=user_id,
        )
        await receipt.insert()  # type: ignore[misc]
        return receipt

    async def bulk_create_read_receipts(
        self, message_ids: List[str], user_id: int
    ) -> int:
        """Bulk-create read receipts."""
        count = 0
        for msg_id in message_ids:
            receipt = ReadReceipt(
                message_id=msg_id,
                user_id=user_id,
            )
            await receipt.insert()  # type: ignore[misc]
            count += 1
        return count

    async def get_unread_message_ids(
        self, conversation_id: str, user_id: int
    ) -> List[str]:
        """Get IDs of unread messages for a user in a conversation."""
        query = Message.find(
            {"conversation_id": conversation_id, "is_deleted": False}
        ).sort("created_at")
        messages = await query.to_list()

        # Get last read message
        receipts = await ReadReceipt.find(
            {"user_id": user_id}
        ).sort("-read_at").limit(1).to_list()

        if not receipts:
            return [str(m.id) for m in messages]

        last_read_id = str(receipts[0].message_id)
        last_read_msg = await Message.get(PydanticObjectId(last_read_id))  # type: ignore[misc]

        if not last_read_msg:
            return [str(m.id) for m in messages]

        # Return messages after last read
        unread = [
            str(m.id) for m in messages
            if m.created_at > last_read_msg.created_at
        ]
        return unread

    async def bulk_mark_read(
        self, conversation_id: str, user_id: int
    ) -> int:
        """Mark all messages in a conversation as read."""
        query = Message.find(
            {"conversation_id": conversation_id, "is_deleted": False}
        ).sort("-created_at")
        messages = await query.to_list()

        if not messages:
            return 0

        # Create receipts for all messages
        for msg in messages:
            receipt = ReadReceipt(
                message_id=str(msg.id),
                user_id=user_id,
            )
            await receipt.insert()  # type: ignore[misc]

        return len(messages)
