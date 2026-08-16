from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.logging_config import setup_logging

import logging
import time

# Route
from app.routes.posts_rout import router as posts_router
from app.routes.comments_rout import router as comment_router
from app.routes.auth_rout import router as auth_router
from app.routes.chat_rout import router as chat_router
from app.services.notification_service import NotificationService
from app.database_mongo import init_mongo

setup_logging("DEBUG")

logger = logging.getLogger(__name__)

notification_service = NotificationService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup."""
    logger.info("=== Application starting ===")

    # MongoDB
    logger.info("Initializing MongoDB...")
    await init_mongo()
    logger.info("MongoDB ready")

    # RabbitMQ
    logger.info("Initializing RabbitMQ...")
    try:
        await notification_service.connect()
    except Exception as e:
        logger.error("RabbitMQ connection failed: %s", e)
    logger.info("RabbitMQ connected")

    logger.info("=== Application ready ===")
    yield

    logger.info("=== Application shutting down ===")
    await notification_service.close()
    logger.info("RabbitMQ disconnected")


app = FastAPI(
    title="Backend API",
    description="Форум, потому что, я не застал времена когда они были популярны",
    version="2013",
    swagger_ui_parameters={"swaggerWithCredentials": True},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
# =====================Route================================
app.include_router(posts_router)
app.include_router(comment_router)
app.include_router(auth_router)
app.include_router(chat_router)

@app.middleware('http')
async def log_requests(request, call_next):
    start = time.perf_counter()
    logger.info('Запрос: %s %s', request.method, request.url.path)
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info('Ответ: %s %s -> %s за %.3fс', request.method, request.url.path, response.status_code, elapsed)
    return response


@app.get('/')
async def default():
    logger.debug('Вызван корневой эндпоинт')
    return {'message': 'swagger /docs'}

