"""Acceso a datos puro de `Contacto`. Tenant-scoped: todo contacto
pertenece a un tenant y se lee/escribe siempre en su contexto.

También vive aquí el constructor de filtros de Audiencias
(`_condicion_a_clausula` y derivados): `ContactoRepository` es quien conoce
la forma real de `variables` en Postgres, así que es quien traduce
`FiltroAudiencia` a SQL -- `audiences` nunca construye SQL ni importa este
módulo (import-linter lo prohíbe), solo llama a `ContactsService`."""

import operator
import re
from datetime import date
from uuid import UUID

from sqlalchemy import (
    ColumnElement,
    Date,
    Numeric,
    Select,
    case,
    cast,
    func,
    not_,
    select,
)

from app.contacts.models.contacto_model import Contacto
from app.contacts.schemas.filtro_schema import Condicion, FiltroAudiencia
from app.core.database.tenant_repository import TenantScopedRepository

_PATRON_NUMERICO = r"^-?\d+(\.\d+)?$"
_PATRON_FECHA_ISO = r"^\d{4}-\d{2}-\d{2}$"
_OPERADORES_ORDEN = {
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
}


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

    async def listar_claves_variables(self) -> list[str]:
        """Claves distintas que aparecen hoy en `variables` de los
        contactos del tenant -- descubrimiento dinámico para que el
        constructor de filtros de Audiencias no dependa de un catálogo
        fijo que Pulso no tiene (ver `SPEC-contactos.md` punto 5)."""
        subconsulta = self.scoped().subquery()
        consulta = select(
            func.jsonb_object_keys(subconsulta.c.variables).label("clave")
        ).distinct()
        resultado = await self.session.execute(consulta)
        return sorted(resultado.scalars().all())

    def _query_por_filtro(self, filtro: FiltroAudiencia) -> Select:
        consulta = self.scoped()
        for condicion in filtro.and_:
            consulta = consulta.where(self._condicion_a_clausula(condicion))
        return consulta

    async def contar_por_filtro(self, filtro: FiltroAudiencia) -> int:
        resultado = await self.session.execute(
            self._query_por_filtro(filtro).with_only_columns(func.count())
        )
        return resultado.scalar_one()

    async def listar_ids_por_filtro(self, filtro: FiltroAudiencia) -> list[int]:
        resultado = await self.session.execute(
            self._query_por_filtro(filtro).with_only_columns(Contacto.id)
        )
        return list(resultado.scalars().all())

    def _condicion_a_clausula(self, condicion: Condicion) -> ColumnElement[bool]:
        if condicion.field == "telefono":
            return self._clausula_telefono(condicion)
        if condicion.field == "creado_en":
            return self._clausula_creado_en(condicion)
        return self._clausula_variable(condicion)

    def _clausula_telefono(self, condicion: Condicion) -> ColumnElement[bool]:
        valor = str(condicion.value)
        if condicion.op == "eq":
            return Contacto.telefono == valor
        if condicion.op == "neq":
            return Contacto.telefono != valor
        return Contacto.telefono.ilike(f"%{valor}%")  # op == "contains"

    def _clausula_creado_en(self, condicion: Condicion) -> ColumnElement[bool]:
        valor_fecha = date.fromisoformat(str(condicion.value))
        columna = cast(Contacto.creado_en, Date)
        if condicion.op == "eq":
            return columna == valor_fecha
        if condicion.op == "neq":
            return columna != valor_fecha
        return _OPERADORES_ORDEN[condicion.op](columna, valor_fecha)

    def _clausula_variable(self, condicion: Condicion) -> ColumnElement[bool]:
        clave = condicion.clave_variable
        if condicion.op == "exists":
            return Contacto.variables.has_key(clave)
        if condicion.op == "not_exists":
            return not_(Contacto.variables.has_key(clave))

        texto = Contacto.variables[clave].as_string()
        if condicion.op == "eq":
            return texto == str(condicion.value)
        if condicion.op == "neq":
            return texto != str(condicion.value)
        if condicion.op == "contains":
            return texto.ilike(f"%{condicion.value}%")
        return self._clausula_variable_ordenada(texto, condicion)

    def _clausula_variable_ordenada(
        self, texto: ColumnElement[str], condicion: Condicion
    ) -> ColumnElement[bool]:
        """`gt`/`gte`/`lt`/`lte` sobre una variable: el valor en BD es
        siempre texto (todo import pasa por `pl.cast(pl.String)`, ver
        `SPEC-contactos.md`), así que se intenta un cast seguro -- numérico
        si el valor del filtro es numérico, fecha ISO si parece fecha, y si
        ninguno aplica se compara como texto. Un valor que no castea nunca
        truena la consulta: la fila simplemente no entra en el resultado."""
        comparar = _OPERADORES_ORDEN[condicion.op]
        valor = condicion.value
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            numero = case(
                (texto.op("~")(_PATRON_NUMERICO), cast(texto, Numeric)),
                else_=None,
            )
            return comparar(numero, valor)
        if isinstance(valor, str) and re.match(_PATRON_FECHA_ISO, valor):
            fecha_columna = case(
                (texto.op("~")(_PATRON_FECHA_ISO), cast(texto, Date)),
                else_=None,
            )
            return comparar(fecha_columna, date.fromisoformat(valor))
        return comparar(texto, str(valor))
