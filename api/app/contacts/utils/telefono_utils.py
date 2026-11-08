"""Normalización de teléfono a E.164. Nunca asume país por defecto: un
número sin código de país se rechaza con un motivo explícito -- decisión
explícita del usuario, no una regla inventada aquí."""

import re

from app.contacts.exceptions import TelefonoInvalidoError, TelefonoSinCodigoDePaisError

_CARACTERES_DE_FORMATO = re.compile(r"[\s\-.()]")
_E164 = re.compile(r"^\+[1-9]\d{6,14}$")

MOTIVO_SIN_CODIGO_PAIS = (
    "El teléfono no incluye código de país (debe empezar con '+'): sin "
    "código es ambiguo y Pulso nunca asume uno por defecto."
)
MOTIVO_FORMATO_INVALIDO = "El teléfono no tiene un formato E.164 válido."


def normalizar_telefono_e164(valor: str) -> str:
    """Quita espacios/guiones/puntos/paréntesis de formato y valida E.164.
    Lanza con el motivo exacto que se guarda en `ContactoRechazado.motivo`."""

    limpio = _CARACTERES_DE_FORMATO.sub("", (valor or "").strip())
    if not limpio.startswith("+"):
        raise TelefonoSinCodigoDePaisError(MOTIVO_SIN_CODIGO_PAIS)
    if not _E164.match(limpio):
        raise TelefonoInvalidoError(MOTIVO_FORMATO_INVALIDO)
    return limpio
