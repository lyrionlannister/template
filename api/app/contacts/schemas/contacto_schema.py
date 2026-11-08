"""Schemas de listado y detalle de contactos."""

from datetime import datetime
from uuid import UUID

from app.core.schemas.base_schema import BaseSchema


class ContactoRespuesta(BaseSchema):
    public_id: UUID
    telefono: str
    variables: dict[str, str]
    creado_en: datetime


class ContactosPaginadosRespuesta(BaseSchema):
    contactos: list[ContactoRespuesta]
    total: int
    pagina: int
    por_pagina: int
