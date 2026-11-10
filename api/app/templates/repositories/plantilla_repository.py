"""Acceso a datos puro de `Plantilla`. Tenant-scoped."""

from uuid import UUID

from sqlalchemy import func

from app.core.database.tenant_repository import TenantScopedRepository
from app.templates.models.plantilla_model import Plantilla


class PlantillaRepository(TenantScopedRepository[Plantilla]):
    model = Plantilla

    async def obtener_por_public_id(self, public_id: UUID) -> Plantilla | None:
        resultado = await self.session.execute(
            self.scoped().where(Plantilla.public_id == public_id)
        )
        return resultado.scalars().first()

    async def listar(self, limite: int, desplazamiento: int) -> list[Plantilla]:
        resultado = await self.session.execute(
            self.scoped()
            .order_by(Plantilla.creado_en.desc())
            .limit(limite)
            .offset(desplazamiento)
        )
        return list(resultado.scalars().all())

    async def contar_total(self) -> int:
        resultado = await self.session.execute(
            self.scoped().with_only_columns(func.count())
        )
        return resultado.scalar_one()
