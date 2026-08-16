from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.dependencies import get_current_user
from app.models.user_model import User
from app.schemas.schemas import PostCreate
from app.services.posts_service import PostService
from app.services.user_service import UserService

router = APIRouter(tags=["Посты"])

@router.get("/posts", status_code=status.HTTP_200_OK)
async def get_all_posts(
    page: int = 1,
    limit: int = 20,
    service: PostService = Depends(),
):
    return await service.get_all_posts(page=page, limit=limit)


@router.get("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def get_post(post_id: int, service: PostService = Depends()):
    result = await service.get_post(post_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден",
        )
    return result

@router.post('/posts/add',status_code=status.HTTP_201_CREATED,)
async def add_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends()
):
    return await service.create_post(data, author_id=current_user.id)