"""Fuente de pago recurrente: tokeniza, crea una preautorización (pasa 3DS
una sola vez) y queda lista para cobros recurrentes sin fricción (ver
`suscripcion_service.py`, tarea siguiente). El flujo de 3DS es asíncrono:
`iniciar` devuelve de inmediato con estado `pendiente`; el frontend hace
polling de `consultar_estado` hasta `disponible`/`fallida`, renderizando el
iframe que Wompi exige en cada paso (`BROWSER_INFO` oculto,
`CHALLENGE` visible -- ver `client/src/billing/`)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.exceptions import LimiteDePlanError
from app.app_platform.services.plan_service import PlanService
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import PASARELA, WompiClient
from app.billing.enums.billing_enums import EstadoFuenteDePago, TipoFuenteDePago
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.repositories.fuente_de_pago_repository import FuenteDePagoRepository
from app.billing.services.suscripcion_service import SuscripcionService

_ESTADO_WOMPI_A_PROPIO = {
    "AVAILABLE": EstadoFuenteDePago.disponible,
    "DECLINED": EstadoFuenteDePago.fallida,
    "ERROR": EstadoFuenteDePago.fallida,
}


class FuenteDePagoNoEncontradaError(ValueError):
    pass


class FuenteDePagoService:
    def __init__(
        self,
        session: AsyncSession,
        wompi_client: WompiClient,
        auth_service: AuthService,
        plan_service: PlanService,
        suscripcion_service: SuscripcionService,
    ):
        self.session = session
        self.repository = FuenteDePagoRepository(session)
        self.wompi_client = wompi_client
        self.auth_service = auth_service
        self.plan_service = plan_service
        self.suscripcion_service = suscripcion_service

    async def _monto_mensual_del_tenant(self, tenant_id: int) -> int:
        """Nunca se confía en un monto que mande el cliente: se relee el
        plan vigente del tenant en el servidor en cada preautorización."""

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
        return int(plan.precio_mensual_cop)

    async def iniciar_preautorizacion(
        self,
        sesion: SesionUsuario,
        token: str,
        acceptance_token: str,
        accept_personal_auth: str,
        marca: str | None = None,
        ultimos_cuatro: str | None = None,
        mes_expiracion: str | None = None,
        anio_expiracion: str | None = None,
        titular: str | None = None,
    ) -> FuenteDePago:
        monto_cop = await self._monto_mensual_del_tenant(sesion.tenant_id)
        fuente_simple = await self.wompi_client.crear_fuente_de_pago(
            tipo="CARD",
            token=token,
            customer_email=sesion.email,
            acceptance_token=acceptance_token,
            accept_personal_auth=accept_personal_auth,
        )

        # Cada token de aceptación se consume al usarse en POST /payment_sources
        # (confirmado en vivo contra el sandbox: reusarlo da 422 "ya fue
        # usado"). La preautorización es una segunda llamada a ese mismo
        # endpoint, así que necesita su propio par de tokens frescos.
        tokens_frescos = await self.wompi_client.obtener_tokens_de_aceptacion()
        preauth = await self.wompi_client.crear_preautorizacion(
            payment_source_id=int(fuente_simple["data"]["id"]),
            customer_email=sesion.email,
            acceptance_token=tokens_frescos["data"]["presigned_acceptance"][
                "acceptance_token"
            ],
            accept_personal_auth=tokens_frescos["data"]["presigned_personal_data_auth"][
                "acceptance_token"
            ],
            amount_in_cents=monto_cop * 100,
            currency="COP",
        )

        fuente = await self.repository.add(
            FuenteDePago(
                tenant_id=sesion.tenant_id,
                tipo=TipoFuenteDePago.tarjeta,
                pasarela=PASARELA,
                id_externo=str(preauth["data"]["id"]),
                estado=EstadoFuenteDePago.pendiente,
                es_recurrente=True,
                marca=marca,
                ultimos_cuatro=ultimos_cuatro,
                mes_expiracion=mes_expiracion,
                anio_expiracion=anio_expiracion,
                titular=titular,
                descripcion="Suscripción",
            )
        )
        await self.session.commit()
        return fuente

    async def consultar_estado(self, sesion: SesionUsuario, public_id: UUID) -> dict:
        fuente = await self.repository.obtener_por_public_id(public_id)
        if fuente is None:
            raise FuenteDePagoNoEncontradaError("Fuente de pago no encontrada.")

        if fuente.estado != EstadoFuenteDePago.pendiente:
            return {
                "estado": fuente.estado.value,
                "pasoActual": None,
                "iframeHtml": None,
            }

        datos = await self.wompi_client.obtener_fuente_de_pago(int(fuente.id_externo))
        status_wompi = datos["data"]["status"]
        three_ds = (datos["data"].get("extra") or {}).get("three_ds_auth") or {}

        nuevo_estado = _ESTADO_WOMPI_A_PROPIO.get(status_wompi)
        if nuevo_estado is not None:
            fuente.estado = nuevo_estado
            await self.repository.update(fuente)
            await self.session.commit()

            if nuevo_estado == EstadoFuenteDePago.disponible and fuente.es_recurrente:
                monto_cop = await self._monto_mensual_del_tenant(sesion.tenant_id)
                await self.suscripcion_service.activar_si_no_existe(
                    sesion.tenant_id, fuente.id, Decimal(monto_cop)
                )

            return {
                "estado": fuente.estado.value,
                "pasoActual": None,
                "iframeHtml": None,
            }

        # PROCESSING o PENDING: sigue en curso, posiblemente con un paso 3DS.
        return {
            "estado": EstadoFuenteDePago.pendiente.value,
            "pasoActual": three_ds.get("current_step"),
            "iframeHtml": three_ds.get("three_ds_method_data"),
        }
