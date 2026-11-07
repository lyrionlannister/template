"""Configuración de conexión a PostgreSQL leída desde variables de entorno."""

from dataclasses import dataclass, field

from sqlalchemy.engine import URL

from app.core.config.env_tools import get_or_throw


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = get_or_throw("DB_HOST")
    port: int = int(get_or_throw("DB_PORT"))
    username: str = get_or_throw("DB_USERNAME")
    password: str = get_or_throw("DB_PASSWORD")
    database_name: str = get_or_throw("DB_NAME")
    database_engine: str = get_or_throw("DB_ENGINE")
    database_driver: str = get_or_throw("DB_DRIVER")
    url_connection: URL = field(init=False)

    def __post_init__(self) -> None:
        # `URL.create()` en vez de un f-string: escapa usuario/contraseña con caracteres
        # especiales (@, :, /), que romperían un string crudo armado a mano.
        object.__setattr__(
            self,
            "url_connection",
            URL.create(
                drivername=f"{self.database_engine}+{self.database_driver}",
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database_name,
            ),
        )


db_config = DatabaseConfig()
