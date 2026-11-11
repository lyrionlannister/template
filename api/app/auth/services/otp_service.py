"""OTP de inicio de sesión: gasto de plataforma, nunca del tenant. Usa
credenciales de plataforma para el envío — nunca el WhatsApp ni el saldo
del tenant que se está autenticando — y no descuenta pool ni saldo de
ningún tenant.

El envío real por WhatsApp sale con la identidad de plataforma
(`MessagingSettings.meta_access_token`/`meta_platform_phone_number_id`,
nunca credenciales de un tenant) y la plantilla de autenticación aprobada
que se crea desde el panel de administrador del sistema
(`PlantillaOtpPlataformaService`). SMS/RCS (Sent, fase 9) sigue sin
cliente -- `_despachar` lanza `NotImplementedError` para esos canales.
"""

import secrets
from datetime import UTC, date, datetime, timedelta

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.auth.enums.auth_enums import CanalOtp
from app.auth.exceptions import (
    CodigoOtpExpiradoError,
    CodigoOtpNoEncontradoError,
    CodigoOtpYaUsadoError,
    LimiteDeIntentosError,
)
from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.usuario_model import Usuario
from app.auth.repositories.codigo_otp_repository import CodigoOtpRepository
from app.core.config.settings import get_settings
from app.core.security.otp_hash import hash_codigo_otp
from app.core.valkey.client import increment_with_ttl, valkey_client
from app.messaging.clients.meta_client import MetaClient
from app.messaging.services.dispatcher_service import proveedor_de
from app.messaging.services.plantilla_otp_plataforma_service import (
    PlantillaOtpPlataformaService,
)

EXPIRACION_MINUTOS = 5
MAXIMO_INTENTOS_FALLIDOS = 5


class OtpService:
    def __init__(
        self,
        repository: CodigoOtpRepository,
        meta_client: MetaClient | None = None,
        plantilla_service: PlantillaOtpPlataformaService | None = None,
        costo_canal_service: CostoCanalService | None = None,
    ):
        self.repository = repository
        self.meta_client = meta_client or MetaClient()
        self.plantilla_service = plantilla_service or PlantillaOtpPlataformaService(
            repository.session, self.meta_client
        )
        self.costo_canal_service = costo_canal_service or CostoCanalService(
            repository.session
        )

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
        if get_settings().app.env == "development":
            print(
                f"[otp-dev] usuario_id={usuario_id} canal={canal.value} codigo={codigo}"
            )
            return
        if canal == CanalOtp.whatsapp:
            await self._despachar_whatsapp(usuario_id, codigo)
            return
        raise NotImplementedError(
            f"Envío real de OTP por {canal.value} pendiente: requiere el cliente de "
            "Sent (fase 9)."
        )

    async def _despachar_whatsapp(self, usuario_id: int, codigo: str) -> None:
        # Pasa por el dispatcher igual que cualquier otro envío de
        # WhatsApp: es la garantía "WhatsApp nunca por Sent.dm" aplicada
        # también aquí, no solo en mensajería de campañas.
        proveedor_de(CanalMensajeria.whatsapp)

        usuario = await self.repository.session.get(Usuario, usuario_id)
        if usuario is None or not usuario.telefono:
            raise ValueError(
                "El usuario no tiene teléfono registrado para OTP por WhatsApp."
            )
        plantilla = await self.plantilla_service.obtener_aprobada()
        if plantilla is None:
            raise ValueError(
                "No hay una plantilla de autenticación de WhatsApp aprobada todavía."
            )

        costo = await self.costo_canal_service.costo_vigente(
            CanalMensajeria.whatsapp, CategoriaMensaje.authentication, date.today()
        )
        if costo is None:
            print(
                "[otp-whatsapp] advertencia: sin costo vigente registrado para "
                "whatsapp/authentication -- se envía igual, sin registrar costo."
            )

        s = get_settings().messaging
        await self.meta_client.enviar_plantilla(
            phone_number_id=s.meta_platform_phone_number_id,
            token_acceso=s.meta_access_token.get_secret_value(),
            telefono_destino=usuario.telefono,
            nombre_plantilla=plantilla.nombre,
            idioma=plantilla.idioma,
            parametros_posicionales=[codigo],
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
