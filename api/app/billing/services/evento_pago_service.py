"""Procesamiento idempotente de eventos entrantes de la pasarela de pago.

Al confirmar un `Cobro` (onboarding, suscripción) el webhook actualiza su
estado y, si es el pago de onboarding aprobado, marca el tenant como pagado
a través de `AuthService` (nunca tocando `auth.models` directo -- ver
`.importlinter`). La recarga de saldo (`MovimientoSaldo`) y la suscripción
recurrente llegan en tareas posteriores y se conectan aquí mismo."""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import PASARELA, verificar_checksum_evento
from app.billing.enums.billing_enums import ConceptoCobro, EstadoTransaccionPago
from app.billing.exceptions import ChecksumInvalidoError
from app.billing.models.evento_pago_procesado_model import EventoPagoProcesado
from app.billing.repositories.cobro_repository import CobroRepository
from app.billing.repositories.evento_pago_repository import EventoPagoRepository
from app.core.database.tenant_context import set_current_tenant

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
    def __init__(self, session: AsyncSession, auth_service: AuthService):
        self.session = session
        self.repository = EventoPagoRepository(session)
        self.cobro_repository = CobroRepository(session)
        self.auth_service = auth_service

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

        nuevo = EventoPagoProcesado(
            tenant_id=cobro.tenant_id if cobro else None,
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
        return creado

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
