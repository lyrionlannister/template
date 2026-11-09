"""Schemas de request/respuesta del dominio templates."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.core.schemas.base_schema import BaseSchema


class PlantillaCrearRequest(BaseSchema):
    nombre: str = Field(min_length=1, max_length=150)
    canal: CanalMensajeria
    contenido: str = Field(min_length=1)
    categoria: CategoriaMensaje | None = None
    nombre_plantilla_meta: str | None = Field(default=None, max_length=512)


class PlantillaActualizarRequest(BaseSchema):
    """Nunca incluye `canal`: es inmutable una vez creada la plantilla."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    contenido: str | None = Field(default=None, min_length=1)
    categoria: CategoriaMensaje | None = None
    nombre_plantilla_meta: str | None = Field(default=None, max_length=512)


class PlantillaRespuesta(BaseSchema):
    public_id: UUID
    nombre: str
    canal: CanalMensajeria
    contenido: str
    variables: list[str]
    categoria: CategoriaMensaje | None
    nombre_plantilla_meta: str | None
    creado_en: datetime


class PlantillasPaginadasRespuesta(BaseSchema):
    plantillas: list[PlantillaRespuesta]
    total: int
    pagina: int
    por_pagina: int


class RenderizarRequest(BaseSchema):
    contacto_public_id: UUID


class RenderizarRespuesta(BaseSchema):
    texto: str


class VerificarAudienciaRequest(BaseSchema):
    audiencia_public_id: UUID


class ContactoConVariableFaltante(BaseSchema):
    contacto_public_id: UUID
    telefono: str
    variables_faltantes: list[str]


class VerificarAudienciaRespuesta(BaseSchema):
    total_contactos: int
    contactos_con_variable_faltante: list[ContactoConVariableFaltante]
