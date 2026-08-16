import json
import logging
from typing import Optional, Sequence
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database import get_db
from app.models.comment_model import Comment
from app.schemas.schemas import CommentOut
from app.services.cache import cache_service
from app.config import get_settings

logger = logging.getLogger(__name__)

CACHE_PREFIX_COMMENTS = "comments_list"


class CommentsRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_comments_by_post(self, post_id: int) -> list[dict]:
        cache_key = f"{CACHE_PREFIX_COMMENTS}:{post_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug("Hit cache for comments: %s", cache_key)
            return json.loads(cached)

        logger.info("Cache miss for comments: %s, querying database", cache_key)

        stmt = (
            select(Comment)
            .options(
                joinedload(Comment.author),
                selectinload(Comment.replies)
            )
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        )
        result = await self.db.execute(stmt)
        comments = result.scalars().all()
        logger.info("Found %d comments for post_id=%s", len(comments), post_id)

        serialized_tree = self._build_comment_tree(comments)
        await cache_service.set(
            cache_key,
            json.dumps(serialized_tree, ensure_ascii=False, default=str),
            ttl=get_settings().COMMENT_LIST_TTL,
        )
        logger.info("Cached %d comments for post_id=%s", len(serialized_tree), post_id)
        return serialized_tree

    async def add_comment(
        self, post_id: int, content: str, author_id: int, parent_id: Optional[int] = None
    ) -> dict:
        logger.info(
            "Creating comment: post_id=%s, author_id=%s, parent_id=%s",
            post_id,
            author_id,
            parent_id,
        )
        comment = Comment(
            post_id=post_id,
            content=content,
            author_id=author_id,
            parent_id = parent_id if parent_id != 0 else None
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        logger.info("Comment created with id=%s", comment.id)

        cache_key = f"{CACHE_PREFIX_COMMENTS}:{post_id}"
        await cache_service.delete(cache_key)
        logger.info("Cache invalidated for key: %s", cache_key)


        return CommentOut(
            id=comment.id,
            post_id=comment.post_id,
            author=comment.author,
            author_id=comment.author_id,
            content=comment.content,
            created_at=comment.created_at,
            replies=[],
        ).model_dump()

    @staticmethod
    def _build_comment_tree(comments: Sequence[Comment]) -> list[dict]:
        nodes: dict[int, dict] = {}
        roots: list[dict] = []

        for c in comments:
            dict_repr = CommentOut.model_validate(c).model_dump(mode="json")
            dict_repr["replies"] = []
            nodes[c.id] = dict_repr

        for c in comments:
            node = nodes[c.id]
            if c.parent_id is not None and c.parent_id in nodes:
                nodes[c.parent_id]["replies"].append(node)
            else:
                roots.append(node)

        return roots