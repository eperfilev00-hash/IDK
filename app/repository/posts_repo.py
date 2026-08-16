# app/repository/posts_repo.py

import json
import logging
from typing import Optional
from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, get_db_session
from app.models.post_model import Post
from app.schemas.schemas import PostCreate, PostOut
from app.services.cache import cache_service
from app.config import get_settings

logger = logging.getLogger(__name__)

CACHE_PREFIX_LIST = "posts_list"
CACHE_PREFIX_DETAIL = "posts_detail"
CACHE_KEY_COUNT = "posts_count"


class PostRepository:
    async def get_all_posts(self, page: int = 1, limit: int = 20) -> list[dict]:
        # --- Шаг 1: Проверка целостности кэша ---
        cached_count = await cache_service.get(CACHE_KEY_COUNT)

        stmt_count = select(func.count(Post.id))
        session = await get_db_session()
        try:
            result = await session.execute(stmt_count)
            db_count = result.scalar()  # <-- внутри try, а не после finally
        finally:
            await session.close()

        if cached_count is not None and int(cached_count) == db_count:
            logger.debug("Cache is fresh (count=%d), reading from cache", db_count)
        else:
            logger.info(
                "Cache stale (cached=%s, db=%d), refreshing...",
                cached_count, db_count,
            )
            await self._refresh_all_pages(limit)

        # --- Шаг 2: Читаем запрошенную страницу из кэша ---
        cache_key = f"{CACHE_PREFIX_LIST}:{page}:{limit}"
        cached = await cache_service.get(cache_key)
        if cached:
            return json.loads(cached)

        logger.warning("Cache key missing after refresh, reading from DB: %s", cache_key)
        return await self._get_posts_from_db(page, limit)

    async def _refresh_all_pages(self, limit: int) -> None:
        """Обновляет кэш для ВСЕХ страниц постов."""
        stmt = (
            select(Post)
            .options(selectinload(Post.author))
            .order_by(Post.id.desc())
        )
        session = await get_db_session()
        try:
            result = await session.execute(stmt)
            posts = result.scalars().all()  # <-- только один раз, внутри try
        finally:
            await session.close()

        await cache_service.set(
            CACHE_KEY_COUNT,
            str(len(posts)),
            ttl=get_settings().POST_LIST_TTL,
        )

        total_pages = (len(posts) + limit - 1) // limit if posts else 1
        for page_num in range(1, total_pages + 1):
            offset = (page_num - 1) * limit
            page_posts = posts[offset:offset + limit]
            serialized = [PostOut.model_validate(p).model_dump() for p in page_posts]
            cache_key = f"{CACHE_PREFIX_LIST}:{page_num}:{limit}"
            await cache_service.set(
                cache_key,
                json.dumps(serialized, default=str, ensure_ascii=False),
                ttl=get_settings().POST_LIST_TTL,
            )

        logger.info("Cache refreshed: %d posts across %d pages", len(posts), total_pages)

    async def _get_posts_from_db(self, page: int, limit: int) -> list[dict]:
        """Читает конкретную страницу из БД и кэширует."""
        offset = (page - 1) * limit
        stmt = (
            select(Post)
            .options(selectinload(Post.author))
            .order_by(Post.id.desc())
            .offset(offset)
            .limit(limit)
        )
        session = await get_db_session()
        try:
            result = await session.execute(stmt)
            posts = result.scalars().all()  # <-- только один раз, внутри try
        finally:
            await session.close()

        serialized = [PostOut.model_validate(p).model_dump() for p in posts]

        cache_key = f"{CACHE_PREFIX_LIST}:{page}:{limit}"
        await cache_service.set(
            cache_key,
            json.dumps(serialized, default=str, ensure_ascii=False),
            ttl=get_settings().POST_LIST_TTL,
        )
        return serialized

    async def get_post(self, post_id: int) -> Optional[dict]:
        cache_key = f"{CACHE_PREFIX_DETAIL}:{post_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug("Hit cache for post detail: %s", cache_key)
            return json.loads(cached)

        stmt = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
        session = await get_db_session()
        try:
            result = await session.execute(stmt)
            post = result.scalar_one_or_none()  # <-- внутри try, а не после finally
        finally:
            await session.close()

        if post is None:
            return None

        serialized = PostOut.model_validate(post).model_dump()
        await cache_service.set(
            cache_key,
            json.dumps(serialized, default=str, ensure_ascii=False),
            ttl=get_settings().POST_DETAIL_TTL,
        )
        return serialized

    async def create_post(self, data: PostCreate, author_id: int, db: AsyncSession = Depends(get_db)) -> dict:
        post = Post(
            author_id=author_id,
            title=data.title,
            description=data.description,
            content=data.content,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)

        await cache_service.delete_pattern(f"{CACHE_PREFIX_LIST}:*")
        await cache_service.delete(CACHE_KEY_COUNT)

        return PostOut.model_validate(post).model_dump()