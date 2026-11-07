"""Rate limiting por IP para endpoints públicos sensibles a fuerza bruta
(login, registro, OTP) — complementa el bloqueo por cuenta de cada service,
que no frena un ataque distribuido entre muchas cuentas."""

from fastapi import HTTPException, Request, status

from app.core.valkey.client import increment_with_ttl


def rate_limit(prefijo: str, maximo_intentos: int, ventana_segundos: int):
    async def _verificar(request: Request) -> None:
        ip = request.client.host if request.client else "desconocida"
        intentos = await increment_with_ttl(
            f"ratelimit:{prefijo}:{ip}", ventana_segundos
        )
        if intentos > maximo_intentos:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Espera un momento antes de volver a intentarlo.",
            )

    return _verificar
