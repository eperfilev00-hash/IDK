import logging
from fastapi import Depends, HTTPException, status

from app.models.user_model import User
from app.repository.users_repo import UsersRepository
from app.schemas.schemas import RegistrData, LoginData
from app.services.security import hash_password, verify_password

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, repo: UsersRepository = Depends()):
        self.repo = repo

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repo.find_user_by_id(user_id)

        
    async def register_user(self, data: RegistrData):
        if await self.repo.exists_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )

        if await self.repo.exists_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким username уже существует"
            )
        hashed_pwd = await hash_password(data.password)
    
        user = await self.repo.registration(data, hashed_password=hashed_pwd)
        return user

    async def login(self, data: LoginData):
        user = await self.repo.find_user(data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Такого пользователя не найдено')
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='Пользователь недоступен')
        
        if not await verify_password(data.password,user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Неверный email или пароль')
        
        return user