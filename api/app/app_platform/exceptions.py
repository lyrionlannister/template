"""Excepciones del dominio app_platform."""


class ReglaDeIncluidosVioladaError(ValueError):
    pass


class LimiteDePlanError(Exception):
    pass


class ParametroComercialFaltanteError(RuntimeError):
    pass
