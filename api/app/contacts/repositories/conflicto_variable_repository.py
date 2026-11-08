"""Acceso a datos puro de `ConflictoVariableContacto`. Tenant-scoped: todo
conflicto pertenece a un tenant y se lee/escribe siempre en su contexto."""

from uuid import UUID

from app.contacts.models.conflicto_variable_model import ConflictoVariableContacto
from app.core.database.tenant_repository import TenantScopedRepository


class ConflictoVariableRepository(TenantScopedRepository[ConflictoVariableContacto]):
    model = ConflictoVariableContacto

    async def obtener_por_public_id(
        self, public_id: UUID
    ) -> ConflictoVariableContacto | None:
        resultado = await self.session.execute(
            self.scoped().where(ConflictoVariableContacto.public_id == public_id)
        )
        return resultado.scalars().first()
