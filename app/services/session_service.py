import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.cache import cache_service
from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionService:
    @staticmethod
    def _session_key(session_id: str) -> str:
        return f'session:{session_id}'

    async def create_session(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)

        session_data = {
            'user_id': user_id,
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(days=7)).isoformat(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'is_active': True,
        }

        await cache_service.set(
            self._session_key(session_id),
            json.dumps(session_data, ensure_ascii=False),
            ttl=get_settings().SESSION_TTL,
        )
        logger.info('Создана сессия %s для пользователя %d', session_id[:8], user_id)
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        raw = await cache_service.get(self._session_key(session_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error('Ошибка декодирования сессии %s', session_id[:8])
            return None

    async def validate_session(self, session_id: str) -> Optional[dict]:
        try:
            session = await self.get_session(session_id)
            
            if not session or not session.get('is_active'):
                return None
            
            if 'expires_at' in session:
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now(timezone.utc) > expires_at.astimezone(timezone.utc):
                    logger.warning("[SESSION VALIDATE] Сессия истекла по expires_at")
                    await self.delete_session(session_id)
                    return None

            return session
        except Exception as e:
            logger.error("[SESSION VALIDATE] Исключение при валидации: %s", e, exc_info=True)
            return None

    async def delete_session(self, session_id: str) -> None:
        await cache_service.delete(self._session_key(session_id))
        logger.info('Сессия %s удалена', session_id[:8])