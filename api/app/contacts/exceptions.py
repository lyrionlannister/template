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


class TelefonoSinCodigoDePaisError(ValueError):
    """El teléfono no empieza en `+`: sin código de país es ambiguo, y
    Pulso nunca asume uno por defecto."""


class TelefonoInvalidoError(ValueError):
    """El teléfono trae `+` pero no es un E.164 válido."""


class ConflictoNoEncontradoError(ValueError):
    """El conflicto no existe o no pertenece a este tenant."""


class ContactoNoEncontradoError(ValueError):
    """El contacto no existe o no pertenece a este tenant."""


class ConflictoYaRevertidoError(ValueError):
    """El conflicto ya fue revertido antes; revertirlo de nuevo pisaría
    el valor que el usuario ya restauró a mano."""
