"""Validador de fortaleza de contraseña, usado por los schemas de registro."""

import re

LONGITUD_MINIMA = 8
_PATRONES_POR_CLASE = (
    re.compile(r"[a-z]"),
    re.compile(r"[A-Z]"),
    re.compile(r"\d"),
    re.compile(r"[^a-zA-Z0-9]"),
)


def validar_fortaleza_password(password: str) -> str:
    """Longitud mínima y al menos 3 de 4 clases de carácter (minúscula,
    mayúscula, dígito, símbolo)."""

    if len(password) < LONGITUD_MINIMA:
        raise ValueError(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres."
        )
    clases_presentes = sum(
        1 for patron in _PATRONES_POR_CLASE if patron.search(password)
    )
    if clases_presentes < 3:
        raise ValueError(
            "La contraseña debe combinar al menos 3 de: minúsculas, mayúsculas, "
            "números y símbolos."
        )
    return password
