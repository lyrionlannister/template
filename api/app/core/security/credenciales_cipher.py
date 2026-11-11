"""Cifrado simétrico reversible para credenciales de proveedor guardadas en
base de datos (hoy: el token de acceso de Meta por conexión de WhatsApp).
Distinto de todo lo demás en `core/security/`, que es hash/HMAC
irreversible -- esto es la primera credencial que hay que poder leer de
vuelta, no solo verificar.

Fernet (AES-128-CBC + HMAC-SHA256 autenticado) con una única llave activa,
leída fresca de `get_settings()` en cada llamada. Sin rotación de llave: si
se rota, todo lo cifrado con la anterior queda ilegible -- no se resuelve
aquí."""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config.settings import get_settings


class CredencialCifradaInvalidaError(ValueError):
    """El texto cifrado no es válido o fue cifrado con otra llave."""


def _fernet() -> Fernet:
    llave = get_settings().messaging.credenciales_cipher_key.get_secret_value()
    return Fernet(llave.encode())


def cifrar(texto_plano: str) -> str:
    return _fernet().encrypt(texto_plano.encode()).decode()


def descifrar(texto_cifrado: str) -> str:
    try:
        return _fernet().decrypt(texto_cifrado.encode()).decode()
    except InvalidToken as error:
        raise CredencialCifradaInvalidaError(
            "El texto cifrado no es válido o la llave de cifrado cambió."
        ) from error
