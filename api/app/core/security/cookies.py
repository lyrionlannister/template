"""Set/clear de las cookies httpOnly de sesión. Los tokens nunca viajan en el
cuerpo JSON (`/CLAUDE.md`, «Auth»): solo en estas cookies."""

from fastapi import Response

from app.core.security.token_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
# Solo el propio endpoint de refresh necesita leer el refresh token: acotar el
# path reduce dónde viaja la cookie más sensible (7 días de vida).
REFRESH_TOKEN_PATH = "/auth/refresh"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path=REFRESH_TOKEN_PATH,
        secure=True,
        httponly=True,
        samesite="lax",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path=REFRESH_TOKEN_PATH)
