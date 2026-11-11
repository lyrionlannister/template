"""Acceso a datos puro de `ConexionWhatsapp`. Tenant-scoped, salvo
`obtener_por_phone_number_id`: debe poder ver conexiones de CUALQUIER
tenant, porque su propósito es detectar que un número ya fue reclamado por
otro -- un `scoped()` ahí ocultaría justo el caso que hay que detectar."""

from uuid import UUID

from sqlalchemy import func, select

from app.core.database.tenant_repository import TenantScopedRepository
from app.messaging.models.conexion_whatsapp_model import ConexionWhatsapp


class ConexionWhatsappRepository(TenantScopedRepository[ConexionWhatsapp]):
    model = ConexionWhatsapp

    async def obtener_por_public_id(self, public_id: UUID) -> ConexionWhatsapp | None:
        resultado = await self.session.execute(
            self.scoped().where(ConexionWhatsapp.public_id == public_id)
        )
        return resultado.scalars().first()

    async def obtener_por_phone_number_id(
        self, phone_number_id: str
    ) -> ConexionWhatsapp | None:
        resultado = await self.session.execute(
            select(ConexionWhatsapp).where(
                ConexionWhatsapp.phone_number_id == phone_number_id
            )
        )
        return resultado.scalars().first()

    async def listar(self) -> list[ConexionWhatsapp]:
        return await self.get_all()

    async def contar_total(self) -> int:
        resultado = await self.session.execute(
            self.scoped().with_only_columns(func.count())
        )
        return resultado.scalar_one()
