import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.models.mongo_models import MessageMongo
from app.models.chat_models import Conversation, Message, ReadReceipt, ConversationParticipant

logger = logging.getLogger(__name__)

_settings = get_settings()

mongo_client = AsyncIOMotorClient(_settings.mongodb_url)
logger.info("Creating MongoDB connection: %s", _settings.mongodb_url)
mongo_database = mongo_client[_settings.mongo_db_name]


async def init_mongo():
    """Initialize Beanie with MongoDB models."""
    await init_beanie(
        database=mongo_database,  # type: ignore[arg-type]
        document_models=[
            MessageMongo,
            Conversation,
            Message,
            ReadReceipt,
            ConversationParticipant,
        ],
    )
    logger.info("MongoDB initialized via Beanie")


async def get_mongo_db():
    """Getter for MongoDB database instance."""
    return mongo_database