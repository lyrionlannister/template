"""Acceso a datos puro de `ContactoRechazado`. Tenant-scoped: toda fila
rechazada pertenece a un tenant y se lee/escribe siempre en su contexto."""

from sqlalchemy import func

from app.contacts.models.contacto_rechazado_model import ContactoRechazado
from app.core.database.tenant_repository import TenantScopedRepository


class ContactoRechazadoRepository(TenantScopedRepository[ContactoRechazado]):
    model = ContactoRechazado

    async def listar_por_importacion(
        self, importacion_id: int, limite: int, desplazamiento: int
    ) -> list[ContactoRechazado]:
        resultado = await self.session.execute(
            self.scoped()
            .where(ContactoRechazado.importacion_id == importacion_id)
            .order_by(ContactoRechazado.id)
            .limit(limite)
            .offset(desplazamiento)
        )
        return list(resultado.scalars().all())

    async def contar_por_importacion(self, importacion_id: int) -> int:
        resultado = await self.session.execute(
            self.scoped()
            .with_only_columns(func.count())
            .where(ContactoRechazado.importacion_id == importacion_id)
        )
        return resultado.scalar_one()
