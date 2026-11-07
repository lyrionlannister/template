"""Procesamiento idempotente de eventos entrantes de la pasarela de pago.

Al confirmar un `Cobro` (onboarding, suscripción) el webhook actualiza su
estado y, si es el pago de onboarding aprobado, marca el tenant como pagado
a través de `AuthService` (nunca tocando `auth.models` directo -- ver
`.importlinter`). La recarga de saldo (`MovimientoSaldo`) y la suscripción
recurrente llegan en tareas posteriores y se conectan aquí mismo."""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import PASARELA, verificar_checksum_evento
from app.billing.enums.billing_enums import (
    ConceptoCobro,
    EstadoSuscripcion,
    EstadoTransaccionPago,
)
from app.billing.exceptions import ChecksumInvalidoError
from app.billing.models.evento_pago_procesado_model import EventoPagoProcesado
from app.billing.repositories.cobro_repository import CobroRepository
from app.billing.repositories.evento_pago_repository import EventoPagoRepository
from app.billing.repositories.movimiento_saldo_repository import (
    MovimientoSaldoRepository,
)
from app.billing.repositories.suscripcion_repository import SuscripcionRepository
from app.billing.services.suscripcion_service import un_mes_despues
from app.core.database.tenant_context import set_current_tenant

_CLAVE_IMPAGO_REINTENTOS_MAX = "impago_reintentos_max"
_CLAVE_IMPAGO_DIAS_ENTRE_REINTENTOS = "impago_dias_entre_reintentos"

_ESTADO_WOMPI_A_PROPIO = {
    "APPROVED": EstadoTransaccionPago.aprobada,
    "DECLINED": EstadoTransaccionPago.rechazada,
    "VOIDED": EstadoTransaccionPago.rechazada,
    "ERROR": EstadoTransaccionPago.error,
}


def _id_evento_externo(payload: dict[str, Any]) -> str:
    """Clave de idempotencia del evento. Para `transaction.updated` (el único
    evento que procesa esta fase) es la transacción + su estado + el
    timestamp del evento: dos entregas del mismo cambio de estado comparten
    clave: cambios de estado distintos de la misma transacción no."""

    transaccion = (payload.get("data") or {}).get("transaction") or {}
    partes = [
        str(transaccion.get("id", "")),
        str(transaccion.get("status", "")),
        str(payload.get("timestamp", "")),
    ]
    return ":".join(partes)


class EventoPagoService:
    def __init__(
        self,
        session: AsyncSession,
        auth_service: AuthService,
        parametro_comercial_service: ParametroComercialService,
    ):
        self.session = session
        self.repository = EventoPagoRepository(session)
        self.cobro_repository = CobroRepository(session)
        self.movimiento_saldo_repository = MovimientoSaldoRepository(session)
        self.suscripcion_repository = SuscripcionRepository(session)
        self.auth_service = auth_service
        self.parametro_comercial_service = parametro_comercial_service

    async def procesar_webhook(
        self, payload: dict[str, Any]
    ) -> EventoPagoProcesado | None:
        """Devuelve el evento persistido si es nuevo, o `None` si ya se había
        procesado antes (idempotencia: no se reprocesa, no se duplica)."""

        if not verificar_checksum_evento(payload):
            raise ChecksumInvalidoError("El checksum del evento no coincide.")

        clave = _id_evento_externo(payload)
        existente = await self.repository.obtener_por_evento_externo(PASARELA, clave)
        if existente is not None:
            return None

        transaccion = (payload.get("data") or {}).get("transaction") or {}
        referencia = transaccion.get("reference")
        cobro = (
            await self.cobro_repository.obtener_por_referencia_global(referencia)
            if referencia
            else None
        )
        movimiento_saldo = (
            await self.movimiento_saldo_repository.obtener_por_referencia_global(
                referencia
            )
            if referencia and cobro is None
            else None
        )

        tenant_id_resuelto = (
            cobro.tenant_id
            if cobro
            else movimiento_saldo.tenant_id if movimiento_saldo else None
        )
        nuevo = EventoPagoProcesado(
            tenant_id=tenant_id_resuelto,
            pasarela=PASARELA,
            id_evento_externo=clave,
            evento=str(payload.get("event", "")),
            payload=payload,
        )
        try:
            creado = await self.repository.add(nuevo)
            await self.session.commit()
        except IntegrityError:
            # Carrera: otra petición concurrente ya insertó el mismo evento
            # (la restricción única de la tabla es la garantía real).
            await self.session.rollback()
            return None

        if cobro is not None:
            await self._reconciliar_cobro(cobro, transaccion.get("status"))
        elif movimiento_saldo is not None:
            await self._reconciliar_movimiento_saldo(
                movimiento_saldo, transaccion.get("status")
            )
        return creado

    async def _reconciliar_movimiento_saldo(
        self, movimiento, status_wompi: str | None
    ) -> None:
        nuevo_estado = _ESTADO_WOMPI_A_PROPIO.get(str(status_wompi))
        if nuevo_estado is None:
            return  # PENDING u otro estado transitorio: nada que confirmar aún.

        with set_current_tenant(movimiento.tenant_id):
            movimiento.estado = nuevo_estado
            await self.movimiento_saldo_repository.update(movimiento)
            await self.session.commit()

    async def _reconciliar_cobro(self, cobro, status_wompi: str | None) -> None:
        nuevo_estado = _ESTADO_WOMPI_A_PROPIO.get(str(status_wompi))
        if nuevo_estado is None:
            return  # PENDING u otro estado transitorio: nada que confirmar aún.

        with set_current_tenant(cobro.tenant_id):
            cobro.estado = nuevo_estado
            await self.cobro_repository.update(cobro)
            await self.session.commit()

            if (
                cobro.concepto == ConceptoCobro.onboarding
                and nuevo_estado == EstadoTransaccionPago.aprobada
            ):
                await self.auth_service.marcar_onboarding_pagado(cobro.tenant_id)

            if cobro.concepto == ConceptoCobro.suscripcion:
                await self._reconciliar_suscripcion(cobro, nuevo_estado)

    async def _reconciliar_suscripcion(
        self, cobro, nuevo_estado: EstadoTransaccionPago
    ) -> None:
        """Ciclo de impago (fase 5, billing): aprobado reinicia los
        reintentos y agenda el próximo cobro; rechazado/error cuenta un
        intento y, si se agotan los permitidos (`impago_reintentos_max`,
        espaciados `impago_dias_entre_reintentos`), suspende el tenant."""

        suscripcion = await self.suscripcion_repository.obtener_activa_del_tenant()
        if suscripcion is None:
            return

        hoy = date.today()
        if nuevo_estado == EstadoTransaccionPago.aprobada:
            suscripcion.intentos_fallidos_consecutivos = 0
            suscripcion.estado = EstadoSuscripcion.activa
            suscripcion.ultima_referencia_transaccion = cobro.referencia
            suscripcion.proxima_fecha_cobro = un_mes_despues(hoy)
            await self.suscripcion_repository.update(suscripcion)
            await self.session.commit()
            return

        reintentos_max = await self.parametro_comercial_service.valor_vigente(
            _CLAVE_IMPAGO_REINTENTOS_MAX, hoy
        )
        dias_entre_reintentos = await self.parametro_comercial_service.valor_vigente(
            _CLAVE_IMPAGO_DIAS_ENTRE_REINTENTOS, hoy
        )
        suscripcion.intentos_fallidos_consecutivos += 1

        if reintentos_max is not None and (
            suscripcion.intentos_fallidos_consecutivos > int(reintentos_max)
        ):
            suscripcion.estado = EstadoSuscripcion.suspendida
            await self.suscripcion_repository.update(suscripcion)
            await self.session.commit()
            await self.auth_service.suspender_tenant(cobro.tenant_id)
            return

        suscripcion.estado = EstadoSuscripcion.en_reintento
        suscripcion.proxima_fecha_cobro = hoy + timedelta(
            days=int(dias_entre_reintentos) if dias_entre_reintentos is not None else 2
        )
        await self.suscripcion_repository.update(suscripcion)
        await self.session.commit()
