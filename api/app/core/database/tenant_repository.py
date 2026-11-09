"""Repository base para modelos de tenant: el único punto donde se construye
una query sobre un modelo `TenantScopedMixin`. Un repository concreto arma su
query a partir de `self.scoped()`, nunca con `select(self.model)` directo —
así el filtro de tenant no depende de que cada autor se acuerde de ponerlo.

Cache-aside: `get_by_id` lee de Valkey antes que de Postgres; en miss, trae
de Postgres y cachea. La key SIEMPRE lleva el tenant (`tabla:tenant:id`): una
key sin tenant sería una fuga entre tenants tan grave como una query sin
filtro. `session.get()` (heredado de `RepositoryBase`) hace la búsqueda por
PK sin pasar por `scoped()`, así que se revalida `tenant_id` después de
leer, antes de cachear o devolver — si no, alguien podría pedir un id de
otro tenant y, con suerte de colisión de PK, leer su fila.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, select

from app.core.database.base import TenantScopedMixin
from app.core.database.repository_base import RepositoryBase
from app.core.database.tenant_context import get_current_tenant_id
from app.core.valkey.client import valkey_client

_CACHE_TTL_SEGUNDOS_DEFAULT = 300


class TenantScopedRepository[ModelT: TenantScopedMixin](RepositoryBase[ModelT]):
    cache_ttl_segundos: int = _CACHE_TTL_SEGUNDOS_DEFAULT

    def scoped(self) -> Select:
        tenant_id = get_current_tenant_id()
        return select(self.model).where(self.model.tenant_id == tenant_id)

    async def get_by_id(self, id_interno: int) -> ModelT | None:
        tenant_id = get_current_tenant_id()
        clave = self._clave_cache(id_interno, tenant_id)

        crudo = await valkey_client.get(clave)
        if crudo is not None:
            return self._deserializar(crudo)

        instancia = await super().get_by_id(id_interno)
        if instancia is None or instancia.tenant_id != tenant_id:
            return None

        await valkey_client.set(
            clave, self._serializar(instancia), ex=self.cache_ttl_segundos
        )
        return instancia

    async def get_all(self) -> list[ModelT]:
        resultado = await self.session.execute(self.scoped())
        return list(resultado.scalars().all())

    async def update(self, instancia: ModelT) -> ModelT:
        actualizada = await super().update(instancia)
        await self._invalidar(actualizada.id, actualizada.tenant_id)
        return actualizada

    async def delete(self, instancia: ModelT) -> None:
        id_interno = instancia.id
        tenant_id = instancia.tenant_id
        await super().delete(instancia)
        await self._invalidar(id_interno, tenant_id)

    def _clave_cache(self, id_interno: int, tenant_id: int) -> str:
        return f"{self.model.__tablename__}:{tenant_id}:{id_interno}"

    async def _invalidar(self, id_interno: int, tenant_id: int) -> None:
        # El tenant lo trae la propia instancia, no el `ContextVar`: `update()`
        # y `delete()` corren a veces fuera de una petición con tenant en
        # contexto (ej. recuperación de password por token, sin sesión
        # todavía) y la instancia ya es la fuente de verdad de su tenant.
        await valkey_client.delete(self._clave_cache(id_interno, tenant_id))

    def _serializar(self, instancia: ModelT) -> str:
        valores: dict[str, Any] = {}
        for columna in self.model.__table__.columns:
            valor = getattr(instancia, columna.name)
            if isinstance(valor, datetime):
                valor = valor.isoformat()
            elif isinstance(valor, uuid.UUID):
                valor = str(valor)
            valores[columna.name] = valor
        return json.dumps(valores)

    def _deserializar(self, crudo: str) -> ModelT:
        datos: dict[str, Any] = json.loads(crudo)
        for columna in self.model.__table__.columns:
            valor = datos.get(columna.name)
            if valor is None:
                continue
            tipo_python = columna.type.python_type
            if tipo_python is datetime and isinstance(valor, str):
                datos[columna.name] = datetime.fromisoformat(valor)
            elif tipo_python is uuid.UUID and isinstance(valor, str):
                datos[columna.name] = uuid.UUID(valor)
        return self.model(**datos)
