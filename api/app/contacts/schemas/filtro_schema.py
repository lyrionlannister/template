"""Filtro de contactos: el contrato que ejecuta `contacts` y que `audiences`
usa para guardar y validar sus audiencias. Lista plana de condiciones unidas
por AND únicamente -- nunca texto libre, nunca SQL. Quien ejecuta el filtro
(`ContactoRepository`) es quien define aquí qué campos y qué operadores
existen, así que la validación de "esto se puede ejecutar" vive junto a la
ejecución misma, no se duplica en otro dominio."""

import re

from pydantic import Field, model_validator

from app.core.schemas.base_schema import BaseSchema

_CLAVE_VARIABLE_SEGURA = re.compile(r"^[a-zA-Z0-9_]+$")
_PREFIJO_VARIABLE = "variables."

CAMPOS_BASE = {
    "telefono": {"eq", "neq", "contains"},
    "creado_en": {"eq", "neq", "gt", "gte", "lt", "lte"},
}
OPERADORES_VARIABLE = {
    "eq",
    "neq",
    "contains",
    "gt",
    "gte",
    "lt",
    "lte",
    "exists",
    "not_exists",
}
_OPERADORES_SIN_VALOR = {"exists", "not_exists"}


class Condicion(BaseSchema):
    field: str
    op: str
    value: str | int | float | None = None

    @model_validator(mode="after")
    def _validar(self) -> Condicion:
        operadores_permitidos = self._operadores_permitidos()
        if operadores_permitidos is None:
            raise ValueError(f"Campo de filtro no permitido: {self.field!r}.")
        if self.op not in operadores_permitidos:
            raise ValueError(
                f"Operador {self.op!r} no permitido para el campo {self.field!r}."
            )
        if self.op in _OPERADORES_SIN_VALOR:
            if self.value is not None:
                raise ValueError(f"El operador {self.op!r} no lleva valor.")
        elif self.value is None:
            raise ValueError(f"El operador {self.op!r} requiere un valor.")
        return self

    def _operadores_permitidos(self) -> set[str] | None:
        if self.field in CAMPOS_BASE:
            return CAMPOS_BASE[self.field]
        if self.field.startswith(_PREFIJO_VARIABLE):
            clave = self.field.removeprefix(_PREFIJO_VARIABLE)
            if clave and _CLAVE_VARIABLE_SEGURA.match(clave):
                return OPERADORES_VARIABLE
        return None

    @property
    def clave_variable(self) -> str:
        return self.field.removeprefix(_PREFIJO_VARIABLE)


class FiltroAudiencia(BaseSchema):
    """Shape fijo del mockup (`resources/Pulso Vistas del Sistema.html`,
    vista "Nueva audiencia"): solo AND, sin grupos anidados, sin OR."""

    and_: list[Condicion] = Field(alias="and")

    @model_validator(mode="after")
    def _no_vacio(self) -> FiltroAudiencia:
        if not self.and_:
            raise ValueError("El filtro necesita al menos una condición.")
        return self
