"""Acceso a datos puro de `Contacto`. Tenant-scoped: todo contacto
pertenece a un tenant y se lee/escribe siempre en su contexto."""

from uuid import UUID

from app.contacts.models.contacto_model import Contacto
from app.core.database.tenant_repository import TenantScopedRepository


class ContactoRepository(TenantScopedRepository[Contacto]):
    model = Contacto

    async def obtener_por_telefono(self, telefono: str) -> Contacto | None:
        resultado = await self.session.execute(
            self.scoped().where(Contacto.telefono == telefono)
        )
        return resultado.scalars().first()

    async def obtener_por_public_id(self, public_id: UUID) -> Contacto | None:
        resultado = await self.session.execute(
            self.scoped().where(Contacto.public_id == public_id)
        )
        return resultado.scalars().first()
