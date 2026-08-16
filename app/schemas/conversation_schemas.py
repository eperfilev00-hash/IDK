from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AuthorInfo(BaseModel):
    """Minimal author information for nested responses."""

    id: int
    username: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationParticipantOut(BaseModel):
    """Participant information inside a conversation."""

    user_id: str
    username: Optional[str] = None
    joined_at: Optional[datetime] = None
    is_muted: bool = False

    model_config = ConfigDict(from_attributes=True)


class ConversationBrief(BaseModel):
    """Brief conversation info for list views."""

    id: str
    type: str
    title: Optional[str] = None
    unread_count: int = 0
    last_message_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    """Full conversation details."""

    id: str
    type: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    unread_count: int = 0
    last_message_id: Optional[str] = None  
    last_message_at: Optional[datetime] = None 
    participants: List[ConversationParticipantOut] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""

    type: str = "private"
    participant_ids: List[int]
    title: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    conversations: List[ConversationBrief]
    total: int
    page: int
    limit: int
