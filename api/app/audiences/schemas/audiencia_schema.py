"""Schemas de request/respuesta del dominio audiences."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.audiences.enums.audiences_enums import TipoAudiencia
from app.contacts.schemas.filtro_schema import FiltroAudiencia
from app.core.schemas.base_schema import BaseSchema


class AudienciaCrearRequest(BaseSchema):
    nombre: str = Field(min_length=1, max_length=150)
    tipo: TipoAudiencia
    filtro: FiltroAudiencia


class AudienciaActualizarRequest(BaseSchema):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    filtro: FiltroAudiencia | None = None


class DuplicarAudienciaRequest(BaseSchema):
    tipo: TipoAudiencia


class VistaPreviaRequest(BaseSchema):
    filtro: FiltroAudiencia


class VistaPreviaRespuesta(BaseSchema):
    conteo: int


class AudienciaRespuesta(BaseSchema):
    public_id: UUID
    nombre: str
    tipo: TipoAudiencia
    filtro: dict
    conteo: int
    congelada_en: datetime | None
    creado_en: datetime


class AudienciasPaginadasRespuesta(BaseSchema):
    audiencias: list[AudienciaRespuesta]
    total: int
    pagina: int
    por_pagina: int


class CampoFiltroRespuesta(BaseSchema):
    field: str
    operadores: list[str]


class CamposDisponiblesRespuesta(BaseSchema):
    campos: list[CampoFiltroRespuesta]
