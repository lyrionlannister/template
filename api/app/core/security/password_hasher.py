"""Hash y verificación de contraseñas con Argon2id, con pepper y rehash
transparente cuando los parámetros de Argon2 cambian de versión."""

import base64

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config.env_tools import get_or_throw


def _decodificar_pepper(valor: str) -> bytes:
    if not valor:
        return b""
    relleno = "=" * (-len(valor) % 4)
    return base64.urlsafe_b64decode(valor + relleno)


class PasswordHasherService:
    def __init__(self, hasher: PasswordHasher | None = None):
        self._hasher = hasher or PasswordHasher()
        self._pepper = _decodificar_pepper(get_or_throw("PASSWORD_PEPPER").strip())

    def _con_pepper(self, password: str) -> str:
        if not self._pepper:
            return password
        return password + self._pepper.decode("utf-8", errors="ignore")

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("La contraseña no puede estar vacía.")
        return self._hasher.hash(self._con_pepper(password))

    def verify_and_maybe_rehash(
        self, hash_guardado: str, password: str
    ) -> tuple[bool, str | None]:
        try:
            valido = self._hasher.verify(hash_guardado, self._con_pepper(password))
        except (InvalidHashError, VerifyMismatchError):
            return False, None
        if valido and self._hasher.check_needs_rehash(hash_guardado):
            return True, self.hash_password(password)
        return valido, None
