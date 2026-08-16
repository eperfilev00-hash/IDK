"""Chat models for MongoDB using Beanie ODM."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from beanie import Document, Indexed


class ConversationType(str, Enum):
    PRIVATE = 'private'
    GROUP = 'group'


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ConversationParticipant(Document):
    """Participant in a conversation."""

    conversation_id: str  # type: ignore[assignment]
    user_id: int  # type: ignore[assignment]
    joined_at: datetime = datetime.utcnow()
    last_read_message_id: Optional[str] = None
    is_muted: bool = False
    left_at: Optional[datetime] = None

    class Settings:
        name = "conversation_participants"
        indexes = [
            "conversation_id",
            "user_id",
            [("conversation_id", 1), ("user_id", 1)],
        ]


class Message(Document):
    """Message document in MongoDB."""

    conversation_id: str  # type: ignore[assignment]
    sender_id: int  # type: ignore[assignment]
    content: str
    content_type: str = "text"
    reply_to_id: Optional[str] = None
    status: MessageStatus = MessageStatus.SENT
    created_at: datetime = datetime.utcnow()
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    attachments: List[dict] = []

    class Settings:
        name = "messages"
        indexes = [
            "conversation_id",
            "sender_id",
            [("conversation_id", 1), ("created_at", -1)],
            "is_deleted",
        ]
        use_state_management = True


class ReadReceipt(Document):
    """Read receipt for tracking message reads."""

    message_id: str  # type: ignore[assignment]
    user_id: int  # type: ignore[assignment]
    read_at: datetime = datetime.utcnow()

    class Settings:
        name = "read_receipts"
        indexes = [
            [("message_id", 1), ("user_id", 1)],
            "user_id",
        ]


class Conversation(Document):
    """Conversation (dialog) document."""

    type: ConversationType = ConversationType.PRIVATE
    title: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    deleted_at: Optional[datetime] = None
    unread_count: int = 0
    last_message_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    participants: List[str] = []  # List of user_ids

    class Settings:
        name = "conversations"
        indexes = [
            "type",
            "created_at",
            "updated_at",
        ]
        use_state_management = True