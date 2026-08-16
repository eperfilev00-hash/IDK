"""Chat routes — CRUD for conversations and messages."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.dependencies import get_current_user
from app.models.user_model import User
from app.schemas.conversation_schemas import (
    ConversationBrief,
    ConversationCreate,
    ConversationOut,
    ConversationListResponse,
)
from app.schemas.message_schemas import MessageCreate, MessageOut, MarkAsReadRequest
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.repository.chat_repo import ChatRepository

router = APIRouter(prefix="/chat", tags=["Chat"])

logger = logging.getLogger(__name__)


# ======================== CONVERSATIONS ========================


@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation."""
    repo = ChatRepository()  # MongoDB repo
    service = ConversationService(repo)
    try:
        conversation = await service.create_conversation(
            user_id=current_user.id,
            participant_ids=data.participant_ids,
            conv_type=data.type,
            title=data.title,
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations", response_model=List[ConversationBrief])
async def list_conversations(
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of user's conversations."""
    repo = ChatRepository()  # MongoDB repo
    service = ConversationService(repo)
    result = await service.get_conversations(
        user_id=current_user.id
    )
    return result["conversations"]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get full conversation details."""
    repo = ChatRepository()  # MongoDB repo
    service = ConversationService(repo)
    conversation = await service.get_conversation_details(
        conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def leave_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Leave (soft-delete) a conversation."""
    repo = ChatRepository()  # MongoDB repo
    service = ConversationService(repo)
    result = await service.leave_conversation(
        conversation_id, current_user.id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"detail": "Conversation left"}


# ======================== MESSAGES ========================


@router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageOut
)
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    """Send a new message to a conversation."""
    if data.content.strip() == "":
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    repo = ChatRepository()  # MongoDB repo
    service = MessageService(repo)
    try:
        message = await service.send_message(
            sender_id=current_user.id,
            conversation_id=conversation_id,
            content=data.content,
            content_type=data.content_type,
            reply_to_id=str(data.reply_to_id) if data.reply_to_id else None,
        )
        return message
    except Exception as e:
        error_msg = str(e)
        if "Rate limit" in error_msg:
            raise HTTPException(status_code=429, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[str] = Query(None),
    after_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Get messages with cursor-based pagination.
    - before_id: messages before this ID (load older)
    - after_id: messages after this ID (load newer)
    """
    repo = ChatRepository()  # MongoDB repo
    service = MessageService(repo)
    messages = await service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        before_id=before_id,
        after_id=after_id,
    )
    return messages


@router.post("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark all messages in a conversation as read."""
    repo = ChatRepository()  # MongoDB repo
    service = MessageService(repo)
    count = await service.mark_as_read(
        conversation_id, current_user.id
    )
    return {"marked": count}


@router.put("/messages/{message_id}/edit")
async def edit_message(
    message_id: str,
    content: str,
    current_user: User = Depends(get_current_user),
):
    """Edit an existing message (only by sender)."""
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    repo = ChatRepository()  # MongoDB repo
    service = MessageService(repo)
    result = await service.edit_message(
        message_id, current_user.id, content
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Message not found or cannot be edited",
        )
    return result


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a message (only by sender)."""
    repo = ChatRepository()  # MongoDB repo
    service = MessageService(repo)
    result = await service.delete_message(
        message_id, current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Message not found or cannot be deleted",
        )
    return {"detail": "Message deleted"}


# ======================== UNREAD ========================


@router.get("/unread")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
):
    """Get total unread message count across all conversations."""
    from app.services.cache import cache_service

    cache_key = f"unread_total:{current_user.id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return {"total_unread": int(cached)}

    # Fallback: count from conversations
    repo = ChatRepository()  # MongoDB repo
    service = ConversationService(repo)
    result = await service.get_conversations(
        current_user.id
    )
    total = sum(c["unread_count"] for c in result["conversations"])

    await cache_service.set(cache_key, str(total), ttl=60)
    return {"total_unread": total}


# ======================== WEBSOCKET ========================


@router.websocket("/ws/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    user_id: int,
):
    """
    WebSocket endpoint for real-time message delivery.
    Connect: ws://host/chat/ws/{user_id}
    """
    from app.services.ws_manager import ws_manager

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif message_type == "subscribe":
                logger.info("user=%d subscribed to events", user_id)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("WS error user=%d: %s", user_id, e)
        ws_manager.disconnect(websocket, user_id)
