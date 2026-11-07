"""Excepciones del dominio contacts."""


class FormatoArchivoNoSoportadoError(ValueError):
    """La extensión del archivo subido no es CSV/XLSX/Parquet."""


class TipoDeArchivoNoCoincideError(ValueError):
    """El contenido real del archivo no corresponde a su extensión."""


class LimiteDeFilasExcedidoError(ValueError):
    """El archivo supera el límite de filas del plan vigente del tenant."""


class PrevisualizacionNoEncontradaError(ValueError):
    """El `preview_id` no existe, ya expiró, ya fue confirmado, o no
    pertenece a este tenant (la clave de Valkey está namespaceada por
    tenant, así que un `preview_id` de otro tenant da el mismo error)."""


class ColumnaTelefonoInvalidaError(ValueError):
    """La columna de teléfono indicada no está entre las columnas
    detectadas del archivo."""
