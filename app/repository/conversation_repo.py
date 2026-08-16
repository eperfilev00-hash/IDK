"""Conversation repository for MongoDB using Beanie."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from beanie import PydanticObjectId

from app.models.chat_models import Conversation, ConversationParticipant, ConversationType

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversations and participants in MongoDB."""

    async def create_conversation(
    self,
    conv_type: str,
    title: Optional[str] = None,
    participant_ids: Optional[List[int]] = None,
    ) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            type=ConversationType(conv_type),
            title=title,
            participants=[str(uid) for uid in (participant_ids or [])],
        )
        await conv.insert() 
        logger.info("Conversation created: %s", conv.id)
        return conv

    async def get_conversation_by_id(self, conv_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        try:
            return await Conversation.get(PydanticObjectId(conv_id))
        except Exception:
            return None

    async def get_conversations_for_user(
        self,
        user_id: int,
    ) -> Tuple[List[Conversation], int]:
        """Get paginated list of conversations for a user."""
        user_str = str(user_id)
        query = Conversation.find({"participants": user_str})
        total = await query.count()
        conversations = await (
            query.sort("-updated_at")
            .to_list()
        )
        return conversations, total

    async def get_conversation_by_users(
        self, user_ids: List[int]
    ) -> Optional[Conversation]:
        """Find a private conversation between specific users."""
        user_ids_str = [str(uid) for uid in user_ids]
        # Beanie не поддерживает .first() на FindMany. Используй find_one.
        conv = await Conversation.find_one(
            {"type": "private", "participants": {"$all": user_ids_str}}
        )
        return conv

    async def add_participants(
        self, conversation_id: str, user_ids: List[int]
    ) -> None:
        """Add participants to a conversation."""
        conv = await Conversation.get(PydanticObjectId(conversation_id))
        if conv:
            conv.participants.extend([str(uid) for uid in user_ids])
            await conv.save_changes()

    async def update_last_message(
        self, conversation_id: str, message_id: str, message_at: datetime
    ) -> None:
        """Update last message reference in a conversation."""
        conv = await Conversation.get(PydanticObjectId(conversation_id))
        if conv:
            conv.last_message_id = message_id
            conv.last_message_at = message_at
            conv.updated_at = datetime.utcnow()
            await conv.save_changes()

    async def increment_unread_count(
        self, conversation_id: str
    ) -> None:
        """Increment unread count for a conversation."""
        conv = await Conversation.get(PydanticObjectId(conversation_id))
        if conv:
            conv.unread_count += 1
            await conv.save_changes()

    async def reset_unread_count(
        self, conversation_id: str
    ) -> None:
        """Reset unread count for a conversation."""
        conv = await Conversation.get(PydanticObjectId(conversation_id))
        if conv:
            conv.unread_count = 0
            await conv.save_changes()
