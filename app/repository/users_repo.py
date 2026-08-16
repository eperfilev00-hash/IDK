# app/repository/users_repo.py
import logging
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user_model import User
from app.schemas.schemas import RegistrData, LoginData

logger = logging.getLogger(__name__)

class UsersRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        logger.debug('UsersRepository инициализирован')


    async def exists_by_email(self, email: EmailStr) -> bool: 
        stmt = select(exists().where(User.email == email))
        result = await self.db.execute(stmt)
        return bool(result.scalar())


    async def exists_by_username(self, username: str) -> bool:
        stmt = select(exists().where(User.username == username))
        result = await self.db.execute(stmt)
        return bool(result.scalar())


    async def find_user(self, email: EmailStr):
        stmt = select(User).where(User.email == email)
        user = await self.db.execute(stmt) 
        return user.scalar_one_or_none()

    async def find_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def registration(self, data: RegistrData, hashed_password: str) -> User:
        new_user = User(
            name=data.name,
            surname=data.surname,
            username=data.username,
            email=data.email,
            hashed_password=hashed_password
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user
