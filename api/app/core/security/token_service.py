"""Emisión y verificación de JWT de acceso/refresh de la sesión.

El token es simple y no autoriza por sí solo: el `access_token` solo prueba
quién dice ser el usuario, nunca lleva rol ni permisos (`/CLAUDE.md`,
«Auth»). La verdad vive en la sesión de Valkey (`session_service.py`).
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config.env_tools import get_or_throw
from app.core.valkey.client import valkey_client

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
# Claim `typ`: acceso y refresh comparten secreto y algoritmo, así que sin él
# un refresh token (7 días) también pasaría como access token.
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class TokenInvalidoError(ValueError):
    pass


class TokenService:
    def __init__(self, secret: str | None = None):
        self._secret = secret or get_or_throw("AUTH_TOKEN_SECRET")

    def generar_access_token(self, usuario_id: int, email: str) -> str:
        ahora = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(usuario_id),
                "typ": ACCESS_TOKEN_TYPE,
                "email": email,
                "iat": ahora,
                "exp": ahora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            },
            self._secret,
            algorithm=ALGORITHM,
        )

    async def generar_refresh_token(self, usuario_id: int) -> str:
        jti = secrets.token_urlsafe(32)
        token = jwt.encode(
            {
                "sub": str(usuario_id),
                "typ": REFRESH_TOKEN_TYPE,
                "jti": jti,
                "exp": datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            },
            self._secret,
            algorithm=ALGORITHM,
        )
        await valkey_client.set(
            self._clave_refresh(usuario_id),
            jti,
            ex=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        )
        return token

    def _decodificar(self, token: str, tipo_esperado: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError as error:
            raise TokenInvalidoError("El token expiró.") from error
        except jwt.InvalidTokenError as error:
            raise TokenInvalidoError("El token no es válido.") from error
        if payload.get("typ") != tipo_esperado or not payload.get("sub"):
            raise TokenInvalidoError("El token no es válido.")
        return payload

    def verificar_access_token(self, token: str) -> dict[str, Any]:
        return self._decodificar(token, ACCESS_TOKEN_TYPE)

    def verificar_refresh_token_jwt(self, token: str) -> dict[str, Any]:
        payload = self._decodificar(token, REFRESH_TOKEN_TYPE)
        if not payload.get("jti"):
            raise TokenInvalidoError("El token no es válido.")
        return payload

    async def refresh_token_vigente(self, usuario_id: int, jti: str) -> bool:
        return await valkey_client.get(self._clave_refresh(usuario_id)) == jti

    async def revocar_refresh_token(self, usuario_id: int) -> None:
        await valkey_client.delete(self._clave_refresh(usuario_id))

    def _clave_refresh(self, usuario_id: int) -> str:
        return f"refresh:{usuario_id}"
