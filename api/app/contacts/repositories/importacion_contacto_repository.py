"""Acceso a datos puro de `ImportacionContacto`. Tenant-scoped: toda
importación pertenece a un tenant y se lee/escribe siempre en su
contexto."""

from uuid import UUID

from app.contacts.models.importacion_contacto_model import ImportacionContacto
from app.core.database.tenant_repository import TenantScopedRepository


class ImportacionContactoRepository(TenantScopedRepository[ImportacionContacto]):
    model = ImportacionContacto

    async def obtener_por_public_id(
        self, public_id: UUID
    ) -> ImportacionContacto | None:
        resultado = await self.session.execute(
            self.scoped().where(ImportacionContacto.public_id == public_id)
        )
        return resultado.scalars().first()
