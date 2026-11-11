"""Conexión de WhatsApp de un tenant vía Embedded Signup: recibe el `code`
de OAuth y los identificadores que el SDK de Meta entrega por
`postMessage` (`waba_id`, `phone_number_id`), canjea el `code` por un
token de acceso y lo guarda cifrado.

Nunca construye SQL de otro dominio -- el plan del tenant se obtiene vía
`AuthService`/`PlanService` (cross-domain permitido vía servicios, nunca
vía `repositories`/`models`, ver `.importlinter`), mismo patrón duplicado
en `AuthService._obtener_plan_del_tenant` / `ContactsService._limite_filas_del_tenant`.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.exceptions import LimiteDePlanError
from app.app_platform.services.plan_service import PlanService
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.auth_service import AuthService
from app.core.security import credenciales_cipher
from app.messaging.clients.meta_client import MetaClient
from app.messaging.exceptions import (
    ConexionWhatsappNoEncontradaError,
    NumeroYaConectadoError,
)
from app.messaging.models.conexion_whatsapp_model import ConexionWhatsapp
from app.messaging.repositories.conexion_whatsapp_repository import (
    ConexionWhatsappRepository,
)


class ConexionWhatsappService:
    def __init__(
        self,
        session: AsyncSession,
        conexion_repository: ConexionWhatsappRepository,
        meta_client: MetaClient,
        auth_service: AuthService,
        plan_service: PlanService,
    ):
        self.session = session
        self.conexion_repository = conexion_repository
        self.meta_client = meta_client
        self.auth_service = auth_service
        self.plan_service = plan_service

    async def _obtener_plan_del_tenant(self, tenant_id: int):
        tenant = await self.auth_service.obtener_tenant(tenant_id)
        if tenant is None or tenant.plan_id is None:
            raise LimiteDePlanError(
                "Esta organización no tiene un plan asignado todavía."
            )
        plan = await self.plan_service.obtener(tenant.plan_id)
        if plan is None:
            raise LimiteDePlanError(
                "El plan asignado a esta organización ya no existe."
            )
        return plan

    async def conectar(
        self,
        sesion: SesionUsuario,
        code: str,
        waba_id: str,
        phone_number_id: str,
    ) -> ConexionWhatsapp:
        existente = await self.conexion_repository.obtener_por_phone_number_id(
            phone_number_id
        )
        if existente is not None:
            raise NumeroYaConectadoError(
                "Este número ya está conectado a otra organización."
            )

        plan = await self._obtener_plan_del_tenant(sesion.tenant_id)
        conteo_actual = await self.conexion_repository.contar_total()
        await self.plan_service.verificar_limite_numeros_whatsapp(plan, conteo_actual)

        intercambio = await self.meta_client.intercambiar_code_por_token(code)
        token_acceso = intercambio["access_token"]
        numero_telefono = await self.meta_client.obtener_numero_telefono(
            phone_number_id, token_acceso
        )

        conexion = ConexionWhatsapp(
            tenant_id=sesion.tenant_id,
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            numero_telefono=numero_telefono,
            token_acceso_cifrado=credenciales_cipher.cifrar(token_acceso),
        )
        conexion = await self.conexion_repository.add(conexion)
        await self.session.commit()
        return conexion

    async def obtener_para_envio(self) -> ConexionWhatsapp:
        """El tenant ya viene del contexto fijado por la sesión de la
        petición (`set_current_tenant`), no de un parámetro: `listar()` lo
        usa vía `scoped()`."""

        conexiones = await self.conexion_repository.listar()
        if not conexiones:
            raise ConexionWhatsappNoEncontradaError(
                "Esta organización no tiene un número de WhatsApp conectado."
            )
        return conexiones[0]

    async def listar(self) -> list[ConexionWhatsapp]:
        return await self.conexion_repository.listar()

    async def obtener(self, public_id: UUID) -> ConexionWhatsapp:
        conexion = await self.conexion_repository.obtener_por_public_id(public_id)
        if conexion is None:
            raise ConexionWhatsappNoEncontradaError(
                "La conexión no existe o no pertenece a esta organización."
            )
        return conexion
