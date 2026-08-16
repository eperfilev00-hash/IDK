"""Chat repository — composition of conversation, message and read receipt repositories."""

import logging

from app.repository.conversation_repo import ConversationRepository
from app.repository.message_repo import MessageRepository
from app.repository.read_receipt_repo import ReadReceiptRepository

logger = logging.getLogger(__name__)


class ChatRepository:
    """Chat repository delegating to specialized sub-repositories.

    Usage:
        repo = ChatRepository()
        conv = await repo.conversations.create_conversation("private")
        msg = await repo.messages.create_message(...)
        receipts = await repo.read_receipts.get_unread_message_ids(...)
    """

    def __init__(self):
        self.conversations = ConversationRepository()
        self.messages = MessageRepository()
        self.read_receipts = ReadReceiptRepository()