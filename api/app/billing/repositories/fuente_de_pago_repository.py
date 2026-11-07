"""Acceso a datos puro de `FuenteDePago`. Tenant-scoped: toda fuente de pago
pertenece a un tenant y se lee/escribe siempre en su contexto."""

from uuid import UUID

from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.core.database.tenant_repository import TenantScopedRepository


class FuenteDePagoRepository(TenantScopedRepository[FuenteDePago]):
    model = FuenteDePago

    async def obtener_por_public_id(self, public_id: UUID) -> FuenteDePago | None:
        resultado = await self.session.execute(
            self.scoped().where(FuenteDePago.public_id == public_id)
        )
        return resultado.scalars().first()
