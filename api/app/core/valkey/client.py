"""Cliente Valkey único y reutilizable para toda la aplicación.

`redis-py` en modo async, apuntando a Valkey (protocolo RESP, ver
`app/core/config/valkey_config.py`). Un solo cliente por proceso: `redis-py`
ya mantiene su propio pool de conexiones internamente.
"""

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config.valkey_config import valkey_config

valkey_client = Redis.from_url(valkey_config.url, decode_responses=True)


async def check_valkey_health() -> bool:
    try:
        return await valkey_client.ping()
    except RedisError:
        return False


async def increment_with_ttl(key: str, ttl_segundos: int) -> int:
    """Contador de ventana fija: `INCR` es atómico; el `EXPIRE` solo se arma en
    el primer incremento para no reiniciar el TTL en cada intento siguiente."""
    valor = await valkey_client.incr(key)
    if valor == 1:
        await valkey_client.expire(key, ttl_segundos)
    return valor
