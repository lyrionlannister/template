"""Excepciones del dominio billing."""


class ChecksumInvalidoError(ValueError):
    """El checksum del evento de la pasarela no coincide. El evento no se
    procesa ni se persiste."""


class OnboardingYaPagadoError(ValueError):
    pass
