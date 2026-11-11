"""Configuración tipada de la aplicación, leída desde variables de entorno
(`.env`) con `pydantic-settings`. Agrupada por dominio, sin mezclarlos.

`get_settings()` es el único punto de acceso: cachea las 6 clases de
configuración (una instancia de proceso), así que una variable obligatoria
que falte tira `ValidationError` al construirse, no un `RuntimeError` al
primer uso como con la lectura de entorno anterior.
"""

from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import quote

from pydantic import BeforeValidator, SecretStr
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import URL

# 3 horas, TTL fijo de la sesión en Valkey (ver `/api/CLAUDE.md`, sección
# "Autenticación y sesión").
VALKEY_SESSION_TTL_SEGUNDOS = 10800


def _csv_a_lista(valor: str | list[str]) -> list[str]:
    if isinstance(valor, list):
        return valor
    return [parte.strip() for parte in valor.split(",") if parte.strip()]


ListaSeparadaPorComas = Annotated[list[str], NoDecode, BeforeValidator(_csv_a_lista)]


class _ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AppSettings(_ConfigBase):
    env: Literal["development", "production"] = "development"
    allowed_origins: ListaSeparadaPorComas = []


class DatabaseSettings(_ConfigBase):
    db_host: str
    db_port: int
    db_username: str
    db_password: SecretStr
    db_name: str
    db_engine: str
    db_driver: str

    @property
    def url_connection(self) -> URL:
        # `URL.create()` en vez de un f-string: escapa usuario/contraseña con
        # caracteres especiales (@, :, /), que romperían un string crudo
        # armado a mano.
        return URL.create(
            drivername=f"{self.db_engine}+{self.db_driver}",
            username=self.db_username,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


class ValkeySettings(_ConfigBase):
    valkey_host: str
    valkey_port: int
    valkey_password: SecretStr

    @property
    def url(self) -> str:
        password = quote(self.valkey_password.get_secret_value(), safe="")
        return f"redis://:{password}@{self.valkey_host}:{self.valkey_port}/0"


class AuthSettings(_ConfigBase):
    auth_token_secret: SecretStr
    password_pepper: SecretStr
    google_client_id: str
    resend_api_key: SecretStr
    resend_from_email: str = "Pulso <onboarding@resend.dev>"
    frontend_url: str = "http://localhost:5173"


class BillingSettings(_ConfigBase):
    wompi_public_key: SecretStr
    wompi_private_key: SecretStr
    wompi_events_secret: SecretStr
    wompi_integrity_secret: SecretStr
    wompi_ambiente: Literal["sandbox", "production"] = "sandbox"


class MessagingSettings(_ConfigBase):
    meta_app_id: str
    meta_app_secret: SecretStr
    meta_config_id: str
    meta_graph_api_version: str = "v27.0"
    credenciales_cipher_key: SecretStr
    # Identidad de WhatsApp de PLATAFORMA (OTP de login): nunca la de un
    # tenant. System user con acceso total sobre la app y la cuenta de
    # WhatsApp de Pulso -- ver /CLAUDE.md "OTP de inicio de sesión".
    meta_access_token: SecretStr
    meta_platform_phone_number_id: str
    meta_platform_waba_id: str
    # SMS/RCS, token único de plataforma (api/CLAUDE.md "Canales y
    # proveedores") -- el tenant nunca aporta sus propias credenciales de
    # Sent.dm, a diferencia de WhatsApp.
    sentdm_api_key: SecretStr
    sentdm_base_url: str = "https://api.sent.dm"


class Settings:
    def __init__(self) -> None:
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.valkey = ValkeySettings()
        self.auth = AuthSettings()
        self.billing = BillingSettings()
        self.messaging = MessagingSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
