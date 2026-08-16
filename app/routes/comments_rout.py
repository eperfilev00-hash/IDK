import logging

from fastapi import APIRouter, Depends, status
from app.dependencies import get_current_user
from app.models.user_model import User
from app.schemas.schemas import CommentCreate
from app.services.comments_service import CommentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Комментарии"])


@router.get("/posts/{post_id}/comments", status_code=status.HTTP_200_OK)
async def get_all_comments(post_id: int, service: CommentService = Depends()):
    logger.info("GET comments requested for post_id=%s", post_id)
    return await service.get_comments(post_id)


@router.post("/posts/{post_id}/comments/add", status_code=status.HTTP_201_CREATED)
async def add_comment(
    post_id: int,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(),
):
    logger.info(
        "POST comment requested: post_id=%s, author_id=%s, parent_id=%s",
        post_id,
        current_user.id,
        body.parent_id,
    )
    return await service.add_comment(
        post_id=post_id,
        content=body.content,
        author_id=current_user.id,
        author=current_user.username,
        parent_id=body.parent_id,
    )