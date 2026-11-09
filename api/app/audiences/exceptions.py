"""Excepciones del dominio audiences."""


class AudienciaNoEncontradaError(ValueError):
    """La audiencia no existe o no pertenece a este tenant."""


class AudienciaEstaticaInmutableError(ValueError):
    """Una audiencia estática ya congeló su snapshot: su filtro no se
    puede editar, solo su nombre. Si se necesita un filtro distinto, se
    duplica como dinámica, se ajusta y se vuelve a congelar."""
