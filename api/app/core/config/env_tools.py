"""Lectura de variables de entorno, obligatorias u opcionales con default."""

import os


def get_or_throw(key: str) -> str:

    assert key, "La clave no puede estar vacía."

    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Variable de entorno '{key}' no encontrada.")
    return value


def get_or_default(key: str, default: str) -> str:
    """Lee una variable de entorno opcional, con default si no está definida o viene
    vacía."""

    assert key, "La clave no puede estar vacía."

    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    return value
