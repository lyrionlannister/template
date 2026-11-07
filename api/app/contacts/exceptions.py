"""Excepciones del dominio contacts."""


class FormatoArchivoNoSoportadoError(ValueError):
    """La extensión del archivo subido no es CSV/XLSX/Parquet."""


class TipoDeArchivoNoCoincideError(ValueError):
    """El contenido real del archivo no corresponde a su extensión."""


class LimiteDeFilasExcedidoError(ValueError):
    """El archivo supera el límite de filas del plan vigente del tenant."""
