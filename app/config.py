import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========= DB ============
    database_url: str

    # ========= MONGODB ============
    mongodb_url: str
    mongo_db_name: str = "idk_mongo"

    # ========= MINIO / S3 ========
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "admin123"
    minio_secure: bool = False

    # ========= REDIS =========
    redis_url: str = "redis://localhost:6379/0"
    POST_LIST_TTL: int = 300
    POST_DETAIL_TTL: int = 300
    COMMENT_LIST_TTL: int = 120
    MESSAGE_TTL: int = 30 * 24 * 60 * 60  # 30 days in Redis PubSub

    # ========= CHAT CACHE KEYS =========
    CONVERSATION_MESSAGES_KEY: str = "chat:messages:"
    CONVERSATION_MESSAGES_TTL: int = 300  # 5 минут
    CONVERSATIONS_LIST_TTL: int = 120  # 2 минуты
    UNREAD_COUNTER_TTL: int = 86400  # 24 часа

    # ========= CHAT PAGINATION =========
    CONVERSATION_PAGE_SIZE: int = 50

    # ========= COOKIE =========
    SESSION_TTL: int = 7 * 24 * 60 * 60  # days
    SESSION_COOKIE_NAME: str = "session_id"

    # ========= RABBITMQ =========
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    rabbitmq_exchange: str = "chat_exchange"
    rabbitmq_queue: str = "notifications"

    # ========= WEBSOCKET =========
    ws_chat_prefix: str = "ws/chat/"

    # ========= RATE LIMIT =========
    rate_limit_messages: int = 30
    rate_limit_window: int = 60  # секунд


@lru_cache
def get_settings() -> Settings:
    settings = Settings() # pyright: ignore[reportCallIssue]
    logger.info("Настройки загружены: redis_url=%s", settings.redis_url)
    return settings