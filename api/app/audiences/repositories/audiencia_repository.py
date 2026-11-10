"""Acceso a datos puro de `Audiencia` y de su snapshot
(`AudienciaContacto`). Tenant-scoped vía `Audiencia`; `AudienciaContacto` no
tiene `tenant_id` propio (hereda el aislamiento de su `Audiencia`, ya
tenant-scoped -- un `audiencia_id` de otro tenant nunca es alcanzable desde
este repository porque siempre se llega a él a través de una `Audiencia` ya
resuelta con `scoped()`)."""

from uuid import UUID

from sqlalchemy import func, select

from app.audiences.models.audiencia_contacto_model import AudienciaContacto
from app.audiences.models.audiencia_model import Audiencia
from app.core.database.tenant_repository import TenantScopedRepository


class AudienciaRepository(TenantScopedRepository[Audiencia]):
    model = Audiencia

    async def obtener_por_public_id(self, public_id: UUID) -> Audiencia | None:
        resultado = await self.session.execute(
            self.scoped().where(Audiencia.public_id == public_id)
        )
        return resultado.scalars().first()

    async def listar(self, limite: int, desplazamiento: int) -> list[Audiencia]:
        resultado = await self.session.execute(
            self.scoped()
            .order_by(Audiencia.creado_en.desc())
            .limit(limite)
            .offset(desplazamiento)
        )
        return list(resultado.scalars().all())

    async def contar_total(self) -> int:
        resultado = await self.session.execute(
            self.scoped().with_only_columns(func.count())
        )
        return resultado.scalar_one()

    async def guardar_snapshot(
        self, audiencia_id: int, contacto_ids: list[int]
    ) -> None:
        if not contacto_ids:
            return
        self.session.add_all(
            [
                AudienciaContacto(audiencia_id=audiencia_id, contacto_id=contacto_id)
                for contacto_id in contacto_ids
            ]
        )
        await self.session.flush()

    async def contar_snapshot(self, audiencia_id: int) -> int:
        resultado = await self.session.execute(
            select(func.count()).where(AudienciaContacto.audiencia_id == audiencia_id)
        )
        return resultado.scalar_one()

    async def listar_contacto_ids_snapshot(self, audiencia_id: int) -> list[int]:
        resultado = await self.session.execute(
            select(AudienciaContacto.contacto_id).where(
                AudienciaContacto.audiencia_id == audiencia_id
            )
        )
        return list(resultado.scalars().all())
