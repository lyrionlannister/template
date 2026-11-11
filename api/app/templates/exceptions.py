"""Excepciones del dominio templates."""


class PlantillaNoEncontradaError(ValueError):
    """La plantilla no existe o no pertenece a este tenant."""


class VariableNoPermitidaError(ValueError):
    """Un placeholder `{{variable}}` del contenido no es un campo base ni
    una clave existente en las variables de los contactos del tenant."""


class CategoriaRequeridaError(ValueError):
    """Una plantilla de WhatsApp necesita categoría (marketing o utility):
    de ella dependen el precio y el consumo del pool de incluidos."""


class NombrePlantillaMetaRequeridoError(ValueError):
    """Una plantilla de WhatsApp necesita el nombre de la plantilla
    aprobada en la cuenta de WhatsApp Business del cliente."""


class NombrePlantillaSentRequeridoError(ValueError):
    """Una plantilla de SMS o RCS necesita el nombre de la plantilla
    aprobada en el dashboard de Sent.dm -- texto libre no sirve para el
    primer contacto con alguien que nunca respondió."""


class ContactoNoEncontradoParaRenderizarError(ValueError):
    """El contacto indicado para el renderizado de prueba no existe o no
    pertenece a este tenant."""


class VariableFaltanteEnRenderizadoError(ValueError):
    """El contacto elegido para el renderizado de prueba no trae alguna de
    las variables que usa la plantilla."""


class AudienciaNoEncontradaParaVerificarError(ValueError):
    """La audiencia indicada para verificar variables faltantes no existe
    o no pertenece a este tenant."""
