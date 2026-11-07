"""Enumeraciones del dominio contacts."""

import enum


class EstadoImportacion(enum.StrEnum):
    pendiente = "pendiente"
    procesando = "procesando"
    completada = "completada"
    fallida = "fallida"


class FormatoArchivoImportacion(enum.StrEnum):
    csv = "csv"
    xlsx = "xlsx"
    parquet = "parquet"
