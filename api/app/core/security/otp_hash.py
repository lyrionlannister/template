"""Hash de códigos OTP: la tabla nunca guarda el código en claro (un volcado
de la base no debe servir para superar el MFA). HMAC-SHA256 ligado al
usuario, con `AUTH_TOKEN_SECRET` como llave — ya es un secreto de entorno
exigido para JWT, no hace falta otro nuevo solo para esto."""

import hmac
from hashlib import sha256

from app.core.config.env_tools import get_or_throw


def hash_codigo_otp(usuario_id: int, codigo: str) -> str:
    llave = get_or_throw("AUTH_TOKEN_SECRET").encode()
    mensaje = f"otp:{usuario_id}:{codigo}".encode()
    return hmac.new(llave, mensaje, sha256).hexdigest()
