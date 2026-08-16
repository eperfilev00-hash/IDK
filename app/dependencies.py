# app/dependencies.py
import logging
from fastapi import Depends, HTTPException, Request, status

from app.config import get_settings
from app.models.user_model import User
from app.repository.users_repo import UsersRepository
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
session_service = SessionService()

async def get_current_user(
    request: Request,
    user_repo: UsersRepository = Depends(),
) -> User:
    cookie_name = get_settings().SESSION_COOKIE_NAME
    session_id = request.cookies.get(cookie_name)
    
    if not session_id:
        raise HTTPException(status_code=401, detail="Не авторизован")

    session = await session_service.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Сессия недействительна или истекла")

    user = await user_repo.find_user_by_id(session['user_id'])
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user

async def get_current_session_id(request: Request) -> str:
    session_id = request.cookies.get(get_settings().SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пользователь не авторизован'
        )
    return session_id