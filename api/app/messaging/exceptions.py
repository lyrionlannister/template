class NumeroYaConectadoError(ValueError):
    """El número ya está conectado a otra organización."""


class ConexionWhatsappNoEncontradaError(ValueError):
    """Esta organización no tiene un número de WhatsApp conectado."""


class VariableFaltanteParaEnvioError(ValueError):
    """El contacto no trae valor para alguna variable de la plantilla."""


class PlantillaOtpPlataformaNoEncontradaError(ValueError):
    """La plantilla de autenticación de WhatsApp de plataforma no existe."""
