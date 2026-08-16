from fastapi import Depends
from app.repository.posts_repo import PostRepository
from app.schemas.schemas import PostCreate

class PostService:
    def __init__(self, repo: PostRepository = Depends()):
        self.repo = repo

    async def get_all_posts(self, page: int = 1, limit: int = 20) -> list[dict]:
        return await self.repo.get_all_posts(page=page, limit=limit)

    async def get_post(self, post_id: int) -> dict | None:
        return await self.repo.get_post(post_id)

    async def create_post(self, data: PostCreate, author_id: int):
        return await self.repo.create_post(data, author_id=author_id)