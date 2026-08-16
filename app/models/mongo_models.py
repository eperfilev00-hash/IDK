from datetime import datetime, timezone
from typing import Optional

from beanie import Document

class MessageMongo(Document):

    sender_id: int 
    receiver_id: int 
    content: str
    is_read: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    attachments: list[str] = []


    class Settings:
        name = "messages"
        indexes = [
            "sender_id",
            "receiver_id",
            ("sender_id", "receiver_id"), 
            "is_read",
        ]