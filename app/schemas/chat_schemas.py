from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AuthorInfo(BaseModel):
    id: int
    username: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============ CONVERSATION ============


class ConversationParticipantOut(BaseModel):
    user_id: int
    username: str
    joined_at: datetime
    is_muted: bool

    model_config = ConfigDict(from_attributes=True)


class ConversationBrief(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    unread_count: int = 0
    last_message_id: Optional[int] = None
    last_message_at: Optional[datetime] = None
    participants_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    type: str = "private"
    participant_ids: List[int]
    title: Optional[str] = None


class ConversationOut(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    unread_count: int = 0
    participants: List[ConversationParticipantOut] = []

    model_config = ConfigDict(from_attributes=True)


# ============ MESSAGE ============


class MessageAttachmentOut(BaseModel):
    id: int
    file_name: str
    file_size: int
    file_type: str
    s3_key: str

    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    sender: AuthorInfo
    body: Optional[str] = None
    body_type: Optional[str] = "text"
    reply_to_id: Optional[int] = None
    attachments: List[MessageAttachmentOut] = []
    status: str = "sent"
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    content_type: str = "text"
    reply_to_id: Optional[int] = None


class ConversationListEntry(BaseModel):
    conversation: ConversationBrief
    last_message: Optional[MessageOut] = None
    participant: Optional[ConversationParticipantOut] = None


# ============ UNREAD ============


class UnreadCountResponse(BaseModel):
    total_unread: int
    conversations: List[ConversationBrief]


class MarkAsReadRequest(BaseModel):
    conversation_id: int
    message_id: Optional[int] = None