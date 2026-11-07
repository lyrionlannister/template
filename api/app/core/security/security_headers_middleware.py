"""Agrega encabezados de seguridad estándar a cada respuesta (OWASP:
scaffold seguro por defecto)."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config.env_tools import get_or_default

ASGIMessage = dict[str, Any]
Receive = Callable[[], Awaitable[ASGIMessage]]
Send = Callable[[ASGIMessage], Awaitable[None]]

_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
]
_HSTS = (b"strict-transport-security", b"max-age=63072000; includeSubDomains")


class SecurityHeadersMiddleware:
    def __init__(self, app) -> None:
        self.app = app
        self._es_produccion = get_or_default("ENV", "development") == "production"

    async def __call__(self, scope: dict, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: ASGIMessage) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend(_HEADERS)
                if self._es_produccion:
                    headers.append(_HSTS)
            await send(message)

        await self.app(scope, receive, send_wrapper)
