"""Middleware anti-CSRF: rechaza peticiones mutantes desde orígenes no
permitidos. La sesión viaja en cookies `SameSite=Lax`, que el navegador sí
adjunta en peticiones GET de navegación cross-site y en algunos POST de
formularios cross-site: SameSite solo no basta. Los navegadores siempre
mandan `Origin` en peticiones mutantes, así que basta
exigir que, si viene, sea uno de `ALLOWED_ORIGINS`. Sin `Origin` no es un
navegador (webhooks, clientes de API) y no aplica."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config.env_tools import get_or_default

ASGIMessage = dict[str, Any]
Receive = Callable[[], Awaitable[ASGIMessage]]
Send = Callable[[ASGIMessage], Awaitable[None]]

_METODOS_MUTANTES = {"POST", "PUT", "PATCH", "DELETE"}


class OriginCheckMiddleware:
    def __init__(self, app) -> None:
        self.app = app
        self._permitidos = {
            origen.strip()
            for origen in get_or_default("ALLOWED_ORIGINS", "").split(",")
            if origen.strip()
        }

    async def __call__(self, scope: dict, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in _METODOS_MUTANTES:
            await self.app(scope, receive, send)
            return

        origen = next(
            (
                valor.decode("latin-1")
                for clave, valor in scope.get("headers", [])
                if clave == b"origin"
            ),
            None,
        )
        if origen is None or origen in self._permitidos:
            await self.app(scope, receive, send)
            return

        cuerpo = json.dumps({"detail": "Origen no permitido."}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(cuerpo)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": cuerpo})
