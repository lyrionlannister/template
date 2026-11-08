"""Verificación del id_token de Google Identity Services (login con Google).

La verificación por firma criptográfica contra las llaves públicas de Google
(`google.oauth2.id_token.verify_oauth2_token`) es la que la propia
documentación de Google recomienda para producción -- el endpoint REST
`tokeninfo` que existe como alternativa está documentado como "solo para
depuración", con posible *throttling* (confirmado en la documentación
oficial de Google Identity, vía Context7, el 2026-11-07).
"""

import asyncio

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config.env_tools import get_or_throw


class GoogleTokenInvalidoError(Exception):
    pass


async def verificar_id_token(token: str) -> str:
    """Verifica firma, audiencia y vigencia del id_token. Devuelve el correo,
    ya confirmado como verificado por Google (`email_verified`)."""

    client_id = get_or_throw("GOOGLE_CLIENT_ID")
    try:
        # Llamada síncrona (descarga/cachea las llaves públicas de Google por
        # HTTP): se corre en un hilo aparte para no bloquear el event loop.
        claims = await asyncio.to_thread(
            id_token.verify_oauth2_token, token, google_requests.Request(), client_id
        )
    except ValueError as error:
        raise GoogleTokenInvalidoError("Token de Google inválido o expirado.") from error

    if not claims.get("email_verified"):
        raise GoogleTokenInvalidoError("El correo de Google no está verificado.")
    email = claims.get("email")
    if not email:
        raise GoogleTokenInvalidoError("El token de Google no incluye un correo.")
    return email
