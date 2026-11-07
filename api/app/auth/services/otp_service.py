"""OTP de inicio de sesión: gasto de plataforma, nunca del tenant
(`/CLAUDE.md`, «OTP de inicio de sesión: gasto interno»). Usa credenciales
de plataforma para el envío — nunca el WhatsApp ni el saldo del tenant que
se está autenticando — y no descuenta pool ni saldo de ningún tenant.

El envío real por WhatsApp (Meta Cloud API, Prompt 05/08) o SMS/RCS (Sent,
Prompt 09) no existe todavía: `_despachar` solo registra el código en modo
desarrollo. Conectar el canal real es una extensión de `_despachar`, no un
cambio de firma, cuando esos clientes existan.
"""

import secrets
from datetime import UTC, datetime, timedelta

from app.auth.enums.auth_enums import CanalOtp
from app.auth.exceptions import (
    CodigoOtpExpiradoError,
    CodigoOtpNoEncontradoError,
    CodigoOtpYaUsadoError,
    LimiteDeIntentosError,
)
from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.repositories.codigo_otp_repository import CodigoOtpRepository
from app.core.config.env_tools import get_or_default
from app.core.security.otp_hash import hash_codigo_otp
from app.core.valkey.client import increment_with_ttl, valkey_client

EXPIRACION_MINUTOS = 5
MAXIMO_INTENTOS_FALLIDOS = 5


class OtpService:
    def __init__(self, repository: CodigoOtpRepository):
        self.repository = repository

    def _clave_intentos(self, usuario_id: int, canal: CanalOtp) -> str:
        return f"otp-intentos:{canal.value}:{usuario_id}"

    async def _exigir_no_bloqueado(self, usuario_id: int, canal: CanalOtp) -> None:
        crudo = await valkey_client.get(self._clave_intentos(usuario_id, canal))
        if crudo is not None and int(crudo) >= MAXIMO_INTENTOS_FALLIDOS:
            raise LimiteDeIntentosError(
                "Demasiados intentos fallidos. Solicita un código nuevo."
            )

    async def enviar(self, tenant_id: int, usuario_id: int, canal: CanalOtp) -> None:
        codigo = str(secrets.randbelow(1_000_000)).zfill(6)
        registro = CodigoOtp(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            canal=canal,
            codigo_hash=hash_codigo_otp(usuario_id, codigo),
            expira_en=datetime.now(UTC) + timedelta(minutes=EXPIRACION_MINUTOS),
        )
        await self.repository.add(registro)
        await self.repository.session.commit()
        await self._despachar(usuario_id, canal, codigo)

    async def _despachar(self, usuario_id: int, canal: CanalOtp, codigo: str) -> None:
        if get_or_default("ENV", "development") == "development":
            print(
                f"[otp-dev] usuario_id={usuario_id} canal={canal.value} codigo={codigo}"
            )
            return
        raise NotImplementedError(
            f"Envío real de OTP por {canal.value} pendiente: requiere el cliente de "
            "plataforma de WhatsApp (Prompt 05/08) o de Sent (Prompt 09)."
        )

    async def verificar(self, usuario_id: int, codigo: str, canal: CanalOtp) -> None:
        await self._exigir_no_bloqueado(usuario_id, canal)
        codigo_hash = hash_codigo_otp(usuario_id, codigo)
        try:
            registro = await self.repository.verificar_con_excepciones(
                usuario_id, codigo_hash, canal
            )
            await self.repository.marcar_consumido(registro)
            await self.repository.session.commit()
        except CodigoOtpNoEncontradoError:
            await increment_with_ttl(
                self._clave_intentos(usuario_id, canal), EXPIRACION_MINUTOS * 60
            )
            raise
        except (CodigoOtpExpiradoError, CodigoOtpYaUsadoError):
            raise
        await valkey_client.delete(self._clave_intentos(usuario_id, canal))
