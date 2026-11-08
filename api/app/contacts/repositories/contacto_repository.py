"""Acceso a datos puro de `Contacto`. Tenant-scoped: todo contacto
pertenece a un tenant y se lee/escribe siempre en su contexto."""

from uuid import UUID

from sqlalchemy import func

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

    def _query_busqueda(self, busqueda_telefono: str | None):
        query = self.scoped()
        if busqueda_telefono:
            query = query.where(Contacto.telefono.ilike(f"%{busqueda_telefono}%"))
        return query

    async def listar(
        self, limite: int, desplazamiento: int, busqueda_telefono: str | None = None
    ) -> list[Contacto]:
        resultado = await self.session.execute(
            self._query_busqueda(busqueda_telefono)
            .order_by(Contacto.id)
            .limit(limite)
            .offset(desplazamiento)
        )
        return list(resultado.scalars().all())

    async def contar(self, busqueda_telefono: str | None = None) -> int:
        resultado = await self.session.execute(
            self._query_busqueda(busqueda_telefono).with_only_columns(func.count())
        )
        return resultado.scalar_one()
