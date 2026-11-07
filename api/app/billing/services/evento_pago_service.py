"""Procesamiento idempotente de eventos entrantes de la pasarela de pago.
Deliberadamente no despacha todavía a ningún handler de dominio (onboarding,
suscripción, recarga): esas tareas no existen aún en este punto del plan.
Cuando existan, consumirán el `EventoPagoProcesado` devuelto por
`procesar_webhook` -- la persistencia idempotente ya es el contrato estable,
el despacho se cablea cuando haya un consumidor real."""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.clients.wompi_client import PASARELA, verificar_checksum_evento
from app.billing.exceptions import ChecksumInvalidoError
from app.billing.models.evento_pago_procesado_model import EventoPagoProcesado
from app.billing.repositories.evento_pago_repository import EventoPagoRepository


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
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventoPagoRepository(session)

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

        nuevo = EventoPagoProcesado(
            tenant_id=None,
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
        return creado
