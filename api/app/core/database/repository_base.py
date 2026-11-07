"""Repository base con las operaciones CRUD comunes a todo modelo: acceso a
datos puro, sin reglas de negocio ni de permisos (eso es el service).
`TenantScopedRepository` extiende esto para datos de tenant (filtro +
cache-aside); un dominio sin datos de tenant (como `app_platform`) lo
extiende directo.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class RepositoryBase[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, instancia: ModelT) -> ModelT:
        self.session.add(instancia)
        await self.session.flush()
        await self.session.refresh(instancia)
        return instancia

    async def get_by_id(self, id_interno: Any) -> ModelT | None:
        return await self.session.get(self.model, id_interno)

    async def get_all(self) -> list[ModelT]:
        resultado = await self.session.execute(select(self.model))
        return list(resultado.scalars().all())

    async def update(self, instancia: ModelT) -> ModelT:
        fusionada = await self.session.merge(instancia)
        await self.session.flush()
        await self.session.refresh(fusionada)
        return fusionada

    async def delete(self, instancia: ModelT) -> None:
        adjunta = await self.session.merge(instancia)
        await self.session.delete(adjunta)
        await self.session.flush()
