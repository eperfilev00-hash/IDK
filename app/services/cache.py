import asyncio
import logging 
import time
from typing import Optional
import uuid

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

redis_pool = redis.ConnectionPool.from_url(
    get_settings().redis_url,
    decode_responses=True,
    max_connections=50, 
)

class CacheService:
    def __init__(self):
        self._redis = redis.Redis(connection_pool=redis_pool, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self._redis.get(key)
            logger.debug("[REDIS GET] Ключ: '%s'", key[:8])
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            return value
        except Exception as e:
            logger.error("[REDIS GET] Ошибка чтения кэша по ключу %s: %s", key, e, exc_info=True)
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self._redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.error("Ошибка записи кэша по ключу %s: %s", key, e)

    async def mset(self, mapping: dict[str, str], ttl: int) -> None:
        """
        Sets multiple keys at once.
        mapping: {key: value}
        """
        try:
            await self._redis.mset(mapping)
            for key in mapping:
                await self._redis.expire(key, ttl)
        except Exception as e:
            logger.error("Ошибка записи нескольких ключей кэша: %s", e)
    
    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error("Ошибка удаления кэша по ключу %s: %s", key, e)

    async def delete_pattern(self, pattern: str) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self._redis.unlink(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error("Ошибка удаления кэша по шаблону %s: %s", pattern, e)

# ============================ SingleFlight / Distributed Mutex ========================

    async def acquire_lock(self, key: str, timeout: int = 5) -> Optional[str]:
        """
        Attempts to acquire a distributed lock (SET NX EX).
        Returns a unique lock_token (str) on success; otherwise, None.
        """
        lock_key = f"mutex:{key}"
        lock_value = str(uuid.uuid4())
        try:
            result = await self._redis.set(
                lock_key, lock_value, nx=True, ex=timeout
            )
            return lock_value if result else None
        except Exception as e:
            logger.error("Ошибка захвата мьютекса по ключу %s: %s", key, e)
            return None

    async def release_lock(self, key: str, lock_value: str) -> None:
        """
        Removes the lock only if lock_value matches.
        Uses a Lua script for atomicity.
        """
        lock_key = f"mutex:{key}"
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            await self._redis.eval(lua_script, 1, lock_key, lock_value)
        except Exception as e:
            logger.error("Ошибка освобождения мьютекса по ключу %s: %s", key, e)

    async def wait_for_cache(self, cache_key: str, max_wait: float = 0.2) -> Optional[str]:
        """
        Waits for a cache maintained by another process to become available.
        Polls Redis every 20 ms, up to max_wait.
        """
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            value = await self.get(cache_key)
            if value:
                return value
            await asyncio.sleep(0.02)
        return None


cache_service = CacheService()