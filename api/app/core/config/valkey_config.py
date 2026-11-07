"""Configuración de conexión a Valkey leída desde variables de entorno.

Valkey es el fork de Redis bajo la Linux Foundation, compatible con el
protocolo RESP: el esquema de la URL sigue siendo
`redis://` porque es parte del protocolo del cliente (`redis-py`), no de la marca
del servidor.
"""

from dataclasses import dataclass, field
from urllib.parse import quote

from app.core.config.env_tools import get_or_throw


@dataclass(frozen=True)
class ValkeyConfig:
    host: str = field(default_factory=lambda: get_or_throw("VALKEY_HOST"))
    port: str = field(default_factory=lambda: get_or_throw("VALKEY_PORT"))
    password: str = field(default_factory=lambda: get_or_throw("VALKEY_PASSWORD"))
    db: str = "0"
    DEFAULT_TTL = 10800  # 3 horas, TTL fijo de la sesión en Valkey

    @property
    def url(self) -> str:
        password = quote(self.password, safe="")
        return f"redis://:{password}@{self.host}:{self.port}/{self.db}"


valkey_config = ValkeyConfig()
