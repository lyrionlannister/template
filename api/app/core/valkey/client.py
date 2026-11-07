"""Cliente Valkey único y reutilizable para toda la aplicación.

`redis-py` en modo async, apuntando a Valkey (protocolo RESP, ver
`app/core/config/valkey_config.py`). Un solo cliente por proceso: `redis-py`
ya mantiene su propio pool de conexiones internamente.
"""

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config.valkey_config import valkey_config

valkey_client = Redis.from_url(valkey_config.url)


async def check_valkey_health() -> bool:
    try:
        return await valkey_client.ping()
    except RedisError:
        return False
