import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
logger.info('Создание движка БД: %s', _settings.database_url)

engine = create_async_engine(_settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    logger.debug('Открытие сессии БД')
    async with AsyncSessionLocal() as session:
        yield session
    logger.debug('Сессия БД закрыта')

async def get_db_session() -> AsyncSession:
    return AsyncSessionLocal()