"""Acceso a datos puro de `eventos_pago_procesados`. No hereda de
`TenantScopedRepository`: un evento no siempre resuelve a un tenant al
llegar (ver docstring del modelo)."""

from sqlalchemy import select

from app.billing.models.evento_pago_procesado_model import EventoPagoProcesado
from app.core.database.repository_base import RepositoryBase


class EventoPagoRepository(RepositoryBase[EventoPagoProcesado]):
    model = EventoPagoProcesado

    async def obtener_por_evento_externo(
        self, pasarela: str, id_evento_externo: str
    ) -> EventoPagoProcesado | None:
        resultado = await self.session.execute(
            select(EventoPagoProcesado).where(
                EventoPagoProcesado.pasarela == pasarela,
                EventoPagoProcesado.id_evento_externo == id_evento_externo,
            )
        )
        return resultado.scalars().first()
