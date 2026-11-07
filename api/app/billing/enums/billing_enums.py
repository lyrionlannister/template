"""Enumeraciones del dominio billing. Nombradas en términos genéricos de
pasarela de pago, no de Wompi: el día que exista una segunda pasarela (no
previsto, pero el nombrado no debería impedirlo), estos valores no cambian.
"""

import enum


class TipoFuenteDePago(enum.StrEnum):
    tarjeta = "tarjeta"
    nequi = "nequi"


class EstadoFuenteDePago(enum.StrEnum):
    pendiente = "pendiente"
    disponible = "disponible"
    fallida = "fallida"


class MedioRecarga(enum.StrEnum):
    tarjeta = "tarjeta"
    pse = "pse"
    nequi = "nequi"


class EstadoTransaccionPago(enum.StrEnum):
    pendiente = "pendiente"
    aprobada = "aprobada"
    rechazada = "rechazada"
    error = "error"


class EstadoSuscripcion(enum.StrEnum):
    pendiente_pago = "pendiente_pago"
    activa = "activa"
    en_reintento = "en_reintento"
    suspendida = "suspendida"
    cancelada = "cancelada"


class ConceptoMovimientoSaldo(enum.StrEnum):
    recarga = "recarga"


class ConceptoCobro(enum.StrEnum):
    """Cargo que no afecta el saldo utilizable del tenant (eso es
    `MovimientoSaldo`): el pago único de onboarding y cada ciclo de la
    suscripción mensual."""

    onboarding = "onboarding"
    suscripcion = "suscripcion"
