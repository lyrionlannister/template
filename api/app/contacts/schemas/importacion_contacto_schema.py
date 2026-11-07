"""Schemas de previsualización de importaciones de contactos."""

from app.core.schemas.base_schema import BaseSchema


class PrevisualizacionImportacionRespuesta(BaseSchema):
    preview_id: str
    columnas: list[str]
    muestra: list[dict[str, str]]
    total_filas: int
