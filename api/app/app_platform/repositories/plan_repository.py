"""Acceso a datos puro de `Plan`."""

from uuid import UUID

from sqlalchemy import select

from app.app_platform.models.plan_model import Plan
from app.core.database.repository_base import RepositoryBase


class PlanRepository(RepositoryBase[Plan]):
    model = Plan

    async def obtener_por_nombre(self, nombre: str) -> Plan | None:
        resultado = await self.session.execute(
            select(Plan).where(Plan.nombre == nombre)
        )
        return resultado.scalars().first()

    async def obtener_por_public_id(self, public_id: UUID) -> Plan | None:
        resultado = await self.session.execute(
            select(Plan).where(Plan.public_id == public_id)
        )
        return resultado.scalars().first()

    async def listar(self) -> list[Plan]:
        resultado = await self.session.execute(select(Plan).order_by(Plan.id))
        return list(resultado.scalars().all())
