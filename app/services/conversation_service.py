"""Conversation service — business logic for dialogs."""

import json
import logging
from typing import List, Optional, Tuple

from app.config import get_settings
from app.repository.chat_repo import ChatRepository
from app.schemas.conversation_schemas import ConversationParticipantOut
from app.services.cache import cache_service

logger = logging.getLogger(__name__)
_settings = get_settings()


class ConversationService:
    """Service for conversation creation, listing and details."""

    def __init__(self, repo: ChatRepository):
        self.repo = repo

    async def create_conversation(
        self,
        user_id: int,
        participant_ids: List[int],
        conv_type: str = "private",
        title: Optional[str] = None,
    ) -> dict:
        """Create a new conversation or return existing one."""
        if conv_type == "private":
            existing = await self.repo.conversations.get_conversation_by_users(
                [user_id] + participant_ids
            )
            if existing:
                logger.info("Existing conversation found: %s", existing.id)
                return self._to_dict(existing)

        conv = await self.repo.conversations.create_conversation(
            conv_type=conv_type, title=title, participant_ids=[user_id] + participant_ids
        )
        logger.info("Conversation created: %s, users: %s", conv.id, [user_id] + participant_ids)
        return self._to_dict(conv)

    async def get_conversations(
        self,
        user_id: int,
    ) -> dict:
        """Get paginated conversation list with caching."""
        cache_key = f"conversations_list:{user_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug("Conversations list cache hit: %s", cache_key)
            return json.loads(cached)

        conversations, total = await self.repo.conversations.get_conversations_for_user(
            user_id=user_id
        )

        result = {
            "conversations": [self._to_brief(c) for c in conversations],
            "total": total,
        }

        await cache_service.set(
            cache_key,
            json.dumps(result, default=str, ensure_ascii=False),
            ttl=_settings.CONVERSATIONS_LIST_TTL,
        )

        return result

    async def get_conversation_details(
        self, conversation_id: str, user_id: int
    ) -> Optional[dict]:
        """Get full conversation details with participants."""
        conv = await self.repo.conversations.get_conversation_by_id(conversation_id)
        if not conv:
            return None

        # Verify user is a participant
        if str(user_id) not in conv.participants:
            raise PermissionError("User is not a participant of this conversation")

        # Reset unread counter when opening conversation
        await self.repo.conversations.reset_unread_count(conversation_id)

        # Invalidate message cache for this conversation
        await cache_service.delete_pattern(f"chat:messages:{conversation_id}:*")

        return self._to_dict(conv)

    async def leave_conversation(
        self, conversation_id: str, user_id: int
    ) -> bool:
        """Soft-delete (leave) a conversation for a specific user."""
        # For MongoDB, we just remove user from participants
        conv = await self.repo.conversations.get_conversation_by_id(conversation_id)
        if conv and str(user_id) in conv.participants:
            conv.participants.remove(str(user_id))
            await conv.save_changes()  # type: ignore[misc]
            await cache_service.delete_pattern(f"chat:messages:{conversation_id}:*")
            return True
        return False

    def _to_dict(self, conv) -> dict:
        """Convert Conversation model to dict."""
        # participants — это список строк ["1", "2"], превращаем в объекты
        participants = [
            ConversationParticipantOut(user_id=str(uid))
            for uid in conv.participants
        ]
        return {
            "id": str(conv.id),
            "type": conv.type.value if hasattr(conv.type, "value") else conv.type,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "unread_count": conv.unread_count,
            "last_message_id": conv.last_message_id,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "participants": participants,
        }

    def _to_brief(self, conv) -> dict:
        """Convert Conversation model to brief dict for list views."""
        return {
            "id": str(conv.id),
            "type": conv.type.value if hasattr(conv.type, "value") else conv.type,
            "title": conv.title,
            "unread_count": conv.unread_count,
            "last_message_id": conv.last_message_id,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "updated_at": conv.updated_at.isoformat(),
        }
