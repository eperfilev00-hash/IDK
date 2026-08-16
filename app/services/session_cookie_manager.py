from typing import Optional

from fastapi import Request, Response

from app.config import get_settings


class SessionCookieManager:

    @staticmethod
    def get_session_id(request: Request) -> Optional[str]:
        return request.cookies.get(get_settings().SESSION_COOKIE_NAME)

        
    @staticmethod
    def set_cookie(response: Response, session_id: str) -> None:
        settings = get_settings()
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            secure=False,        # включить в production
            samesite="lax",
            max_age=settings.SESSION_TTL,
            path="/",
        )

    @staticmethod
    def delete_cookie(response: Response) -> None:
        settings = get_settings()
        response.delete_cookie(
            key=settings.SESSION_COOKIE_NAME,
            path="/",
        )