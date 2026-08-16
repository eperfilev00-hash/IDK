from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class MessageAttachmentOut(BaseModel):
    """Attachment information for a message."""

    id: str
    file_name: str
    file_size: int
    file_type: str
    s3_key: str

    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    """Full message representation."""

    id: str
    sender_id: int
    sender: Optional[dict] = None  # AuthorInfo serialized
    body: Optional[str] = None
    body_type: Optional[str] = "text"
    reply_to_id: Optional[str] = None
    attachments: List[MessageAttachmentOut] = []
    status: str = "sent"
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Request to create a new message."""

    content: str
    content_type: str = "text"
    reply_to_id: Optional[str] = None


class MarkAsReadRequest(BaseModel):
    """Request to mark messages as read."""

    message_id: Optional[int] = None  # optional cursor for partial read
