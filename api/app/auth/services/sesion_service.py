"""Sesión real del usuario en Valkey. TTL de 3 horas (`/CLAUDE.md`, «Auth»):
la sesión no se vincula a dispositivo ni IP — un access token robado solo
sirve mientras la sesión exista en Valkey; la mitigación es la expiración
corta más la revocación inmediata en logout y cambio de contraseña, no un
vínculo a dispositivo.
"""

from app.auth.models.usuario_model import Usuario
from app.auth.schemas.sesion_schema import (
    SesionUsuario,
    clave_mfa_verificado,
    clave_sesion,
)
from app.core.valkey.client import valkey_client

TTL_SESION_SEGUNDOS = 3 * 60 * 60


class SesionService:
    async def construir_y_guardar(self, usuario: Usuario) -> SesionUsuario:
        sesion = SesionUsuario(
            usuario_id=usuario.id,
            tenant_id=usuario.tenant_id,
            email=usuario.email,
            rol=usuario.rol,
            mfa_habilitado=usuario.mfa_habilitado,
        )
        await valkey_client.set(
            clave_sesion(usuario.id),
            sesion.model_dump_json(),
            ex=TTL_SESION_SEGUNDOS,
        )
        return sesion

    async def cargar(self, usuario_id: int) -> SesionUsuario | None:
        crudo = await valkey_client.get(clave_sesion(usuario_id))
        if crudo is None:
            return None
        return SesionUsuario.model_validate_json(crudo)

    async def renovar_ttl(self, usuario_id: int) -> None:
        await valkey_client.expire(clave_sesion(usuario_id), TTL_SESION_SEGUNDOS)

    async def eliminar(self, usuario_id: int) -> None:
        await valkey_client.delete(clave_sesion(usuario_id))
        await valkey_client.delete(clave_mfa_verificado(usuario_id))

    async def marcar_mfa_verificado(self, usuario_id: int) -> None:
        await valkey_client.set(
            clave_mfa_verificado(usuario_id), "1", ex=TTL_SESION_SEGUNDOS
        )

    async def mfa_fue_verificado(self, usuario_id: int) -> bool:
        return await valkey_client.get(clave_mfa_verificado(usuario_id)) is not None

    async def invalidar_mfa(self, usuario_id: int) -> None:
        await valkey_client.delete(clave_mfa_verificado(usuario_id))
