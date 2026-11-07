"""Acceso a datos de `Usuario`. Tenant-scoped vía `TenantScopedRepository`,
salvo dos búsquedas que corren antes de que exista tenant en contexto:

- `obtener_por_email_global`: el login identifica primero a qué tenant
  pertenece un correo.
- `obtener_por_id_global`: `refrescar()` solo tiene el `usuario_id` que ya
  traía el refresh token firmado por Pulso -- el JWT válido ya es la prueba
  de identidad, no hace falta (ni se puede, todavía) tenant en contexto
  para esa única lectura.

Ningún otro método de este repository se salta `scoped()`.
"""

from sqlalchemy import select

from app.auth.models.usuario_model import Usuario
from app.core.database.tenant_repository import TenantScopedRepository


class UsuarioRepository(TenantScopedRepository[Usuario]):
    model = Usuario

    async def obtener_por_email_global(self, email: str) -> Usuario | None:
        resultado = await self.session.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return resultado.scalars().first()

    async def obtener_por_id_global(self, usuario_id: int) -> Usuario | None:
        # No `super().get_by_id()`: `TenantScopedRepository` ya sobreescribe
        # `get_by_id` con la versión que exige tenant en contexto -- `super()`
        # sigue el MRO hasta ahí, no hasta `RepositoryBase`. PK directo.
        return await self.session.get(Usuario, usuario_id)
