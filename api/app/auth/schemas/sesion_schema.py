"""Forma de la sesión de usuario en Valkey y las claves derivadas de su
ciclo de vida. No es una tabla."""

from app.auth.enums.auth_enums import RolUsuario
from app.core.schemas.base_schema import BaseSchema

PREFIJO_SESION = "session:"
PREFIJO_MFA_VERIFICADO = "mfa_verified:"


def clave_sesion(usuario_id: int) -> str:
    return f"{PREFIJO_SESION}{usuario_id}"


def clave_mfa_verificado(usuario_id: int) -> str:
    """Aparte de `SesionUsuario` a propósito: si viviera dentro de la sesión,
    cualquier refresco de sesión (p. ej. tras cambiar de rol) volvería a
    pedir MFA. Solo un login nuevo debe volver a exigirlo."""

    return f"{PREFIJO_MFA_VERIFICADO}{usuario_id}"


class SesionUsuario(BaseSchema):
    usuario_id: int
    tenant_id: int
    email: str
    rol: RolUsuario
    mfa_habilitado: bool
