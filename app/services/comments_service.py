import logging
from typing import Optional

from fastapi import Depends

from app.repository.comments_repo import CommentsRepository
from app.services.content_filter import filter_comment_content

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, repo: CommentsRepository = Depends()):
        self.repo = repo

    async def get_comments(self, post_id: int) -> list[dict]:
        logger.info("Получение комментариев с поста post_id=%s", post_id)
        return await self.repo.get_comments_by_post(post_id)

    async def add_comment(
        self, post_id: int, content: str, author_id: int, author: str, parent_id: Optional[int] = None
    ) -> dict:
        logger.info(
            "Добавление комментария: post_id=%s, author_id=%s, parent_id=%s",
            post_id,
            author_id,
            parent_id,
        )
        filtered_content = filter_comment_content(content)

        return await self.repo.add_comment(
            post_id=post_id,
            content=filtered_content,
            author_id=author_id,
            parent_id=parent_id,
        )