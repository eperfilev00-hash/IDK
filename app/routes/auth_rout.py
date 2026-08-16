import logging
from fastapi import APIRouter, Depends, Request, status, Response

from app.dependencies import get_current_session_id, get_current_user
from app.models.user_model import User
from app.schemas.schemas import RegistrData, LoginData, RegistrResponse
from app.services.session_service import SessionService
from app.services.user_service import UserService 
from app.services.session_cookie_manager import SessionCookieManager

router = APIRouter(tags=['Регистрация'])
logger = logging.getLogger(__name__)

@router.post('/registration',response_model=RegistrResponse, status_code=status.HTTP_201_CREATED)
async def registration(
    data: RegistrData,
    user_service: UserService = Depends()  
):
    user = await user_service.register_user(data)
    return user


@router.post('/login',status_code=status.HTTP_200_OK)
async def login(
    data: LoginData,
    response: Response,
    request: Request,
    user_service: UserService = Depends(),
    session_service: SessionService = Depends()
):
    user = await user_service.login(data)

    session_id = await session_service.create_session(
        user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )
    SessionCookieManager.set_cookie(response,session_id)
    return user


@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    session_id: str = Depends(get_current_session_id),
    session_service: SessionService = Depends()
):
    await session_service.delete_session(session_id)
    SessionCookieManager.delete_cookie(response)
    return {'msg': 'Вы вышли из аккаунта'}

@router.get('/me',response_model=RegistrResponse)
async def me(
    current_user: User = Depends(get_current_user)
):
    return current_user
