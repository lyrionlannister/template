"""Suscripción mensual: se activa cuando una fuente de pago recurrente queda
`disponible` (ver `fuente_de_pago_service.py`) y se cobra sola cada ciclo
mediante `cobrar_ciclo`, invocada por la tarea programada de
`app/billing/scheduler.py` (APScheduler dentro del proceso de la API --
decisión confirmada por Luis el 2026-11-07, sin infraestructura nueva).

El resultado de cada cobro (aprobado/rechazado) lo decide el webhook, nunca
la respuesta inmediata de la pasarela (ver `evento_pago_service.py`): aquí
solo se crea el intento."""

import calendar
import uuid
from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.services.plan_service import PlanService
from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import WompiClient
from app.billing.enums.billing_enums import (
    ConceptoCobro,
    EstadoFuenteDePago,
    EstadoSuscripcion,
    EstadoTransaccionPago,
)
from app.billing.models.cobro_model import Cobro
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.models.suscripcion_model import Suscripcion
from app.billing.repositories.cobro_repository import CobroRepository
from app.billing.repositories.fuente_de_pago_repository import FuenteDePagoRepository
from app.billing.repositories.suscripcion_repository import SuscripcionRepository
from app.core.database.tenant_context import set_current_tenant


def un_mes_despues(fecha: date) -> date:
    mes = fecha.month + 1
    anio = fecha.year + (1 if mes > 12 else 0)
    mes = mes if mes <= 12 else 1
    ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
    return fecha.replace(year=anio, month=mes, day=min(fecha.day, ultimo_dia_mes))


class SuscripcionService:
    def __init__(
        self,
        session: AsyncSession,
        wompi_client: WompiClient,
        auth_service: AuthService,
        plan_service: PlanService,
    ):
        self.session = session
        self.repository = SuscripcionRepository(session)
        self.fuente_repository = FuenteDePagoRepository(session)
        self.cobro_repository = CobroRepository(session)
        self.wompi_client = wompi_client
        self.auth_service = auth_service
        self.plan_service = plan_service

    async def activar_si_no_existe(
        self, tenant_id: int, fuente_de_pago_id: int, monto_cop: Decimal
    ) -> Suscripcion:
        """Si ya hay una suscripción activa, "cambiar tarjeta" apunta su
        cobro a la fuente de pago nueva (la vieja queda huérfana, no se
        borra: sigue en `fuentes_de_pago` como historial). Si no hay
        ninguna, crea la suscripción."""

        existente = await self.repository.obtener_activa_del_tenant()
        if existente is not None:
            existente.fuente_de_pago_id = fuente_de_pago_id
            await self.repository.update(existente)
            await self.session.commit()
            return existente
        nueva = await self.repository.add(
            Suscripcion(
                tenant_id=tenant_id,
                fuente_de_pago_id=fuente_de_pago_id,
                estado=EstadoSuscripcion.activa,
                monto_cop=monto_cop,
                proxima_fecha_cobro=un_mes_despues(date.today()),
                intentos_fallidos_consecutivos=0,
            )
        )
        await self.session.commit()
        return nueva

    async def consultar_estado(self) -> Suscripcion | None:
        """Requiere tenant en contexto (sesión normal del tenant, no la tarea
        programada): lo usa `GET /billing/suscripcion/estado` del frontend."""

        return await self.repository.obtener_activa_del_tenant()

    async def consultar_fuente_de_pago(
        self, suscripcion: Suscripcion
    ) -> FuenteDePago | None:
        if suscripcion.fuente_de_pago_id is None:
            return None
        return await self.fuente_repository.get_by_id(suscripcion.fuente_de_pago_id)

    async def cobrar_ciclo(self) -> int:
        """Entrypoint de la tarea programada. Devuelve cuántas suscripciones
        se intentaron cobrar hoy (no cuántas quedaron aprobadas: eso lo
        confirma el webhook)."""

        hoy = date.today()
        vencidas = await self.repository.obtener_vencidas_global(hoy)
        procesadas = 0
        for suscripcion in vencidas:
            with set_current_tenant(suscripcion.tenant_id):
                if await self._ya_hay_cobro_pendiente_hoy(suscripcion):
                    continue
                await self._cobrar_una(suscripcion)
                procesadas += 1
        return procesadas

    async def _ya_hay_cobro_pendiente_hoy(self, suscripcion: Suscripcion) -> bool:
        """Salvaguarda de idempotencia: si la tarea programada corriera dos
        veces el mismo día (reinicio del proceso, solapamiento), no se
        duplica el intento mientras el anterior sigue sin confirmar."""

        pendientes = [
            c
            for c in await self.cobro_repository.get_all()
            if c.concepto == ConceptoCobro.suscripcion
            and c.estado == EstadoTransaccionPago.pendiente
            and c.creado_en.date() == date.today()
        ]
        return len(pendientes) > 0

    async def _cobrar_una(self, suscripcion: Suscripcion) -> None:
        if suscripcion.fuente_de_pago_id is None:
            return
        fuente: FuenteDePago | None = await self.fuente_repository.get_by_id(
            suscripcion.fuente_de_pago_id
        )
        if (
            fuente is None
            or fuente.estado != EstadoFuenteDePago.disponible
            or not fuente.es_recurrente
        ):
            return

        email = await self.auth_service.obtener_email_administrador(
            suscripcion.tenant_id
        )
        if email is None:
            return

        referencia = f"suscripcion-{suscripcion.tenant_id}-{uuid.uuid4().hex[:12]}"
        cobro = await self.cobro_repository.add(
            Cobro(
                tenant_id=suscripcion.tenant_id,
                concepto=ConceptoCobro.suscripcion,
                fuente_de_pago_id=fuente.id,
                monto_cop=suscripcion.monto_cop,
                estado=EstadoTransaccionPago.pendiente,
                referencia=referencia,
                id_externo_transaccion=None,
            )
        )
        await self.session.commit()

        try:
            transaccion = await self.wompi_client.crear_transaccion(
                reference=referencia,
                amount_in_cents=int(suscripcion.monto_cop) * 100,
                currency="COP",
                customer_email=email,
                payment_source_id=int(fuente.id_externo),
            )
        except httpx.HTTPError:
            cobro.estado = EstadoTransaccionPago.error
            await self.cobro_repository.update(cobro)
            await self.session.commit()
            return

        cobro.id_externo_transaccion = str(transaccion["data"]["id"])
        await self.cobro_repository.update(cobro)
        await self.session.commit()
