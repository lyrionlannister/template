"""Schemas de previsualización y confirmación de importaciones de
contactos."""

from uuid import UUID

from app.contacts.enums.contacts_enums import EstadoImportacion
from app.core.schemas.base_schema import BaseSchema


class PrevisualizacionImportacionRespuesta(BaseSchema):
    preview_id: str
    columnas: list[str]
    muestra: list[dict[str, str]]
    total_filas: int


class ConfirmarImportacionRequest(BaseSchema):
    preview_id: str
    columna_telefono: str
    mapeo_variables: dict[str, str]


class ImportacionContactoRespuesta(BaseSchema):
    public_id: UUID
    estado: EstadoImportacion
    total_filas: int


class EstadoImportacionRespuesta(BaseSchema):
    public_id: UUID
    estado: EstadoImportacion
    total_filas: int
    filas_aceptadas: int
    filas_rechazadas: int
    filas_con_advertencia: int
    motivo_fallo: str | None


class ContactoRechazadoRespuesta(BaseSchema):
    fila_cruda: dict[str, str]
    motivo: str


class RechazosPaginadosRespuesta(BaseSchema):
    rechazos: list[ContactoRechazadoRespuesta]
    total: int
    pagina: int
    por_pagina: int
