"""Excepciones del dominio auth."""


class CodigoOtpNoEncontradoError(Exception):
    pass


class CodigoOtpExpiradoError(Exception):
    pass


class CodigoOtpYaUsadoError(Exception):
    pass


class CredencialesInvalidasError(Exception):
    pass


class LimiteDeIntentosError(Exception):
    pass


class PermisoInsuficienteError(PermissionError):
    pass


class TokenRecuperacionInvalidoError(Exception):
    pass


class CuentaGoogleNoRegistradaError(Exception):
    pass


class EnvioDeCorreoFallidoError(Exception):
    pass
