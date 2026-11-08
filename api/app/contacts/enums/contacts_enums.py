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


class PoliticaConflictoVariables(enum.StrEnum):
    """Qué hacer cuando, al fusionar variables, la clave ya tiene un valor
    no vacío y la fila nueva trae un valor distinto también no vacío.
    Cualquiera que sea la política activa, el conflicto siempre se
    registra en `ConflictoVariableContacto` -- la política solo decide si
    el valor nuevo se aplica o no, nunca si se audita."""

    ultimo_gana = "ultimo_gana"
    no_pisar_marcar_advertencia = "no_pisar_marcar_advertencia"
