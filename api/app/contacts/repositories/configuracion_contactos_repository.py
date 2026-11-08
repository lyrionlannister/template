"""Acceso a datos puro de `ConfiguracionContactos`. Una fila por tenant,
creada bajo demanda -- este repository no inventa la fila por defecto, eso
es decisión del service (`ContactsService.obtener_politica_conflicto`)."""

from app.contacts.models.configuracion_contactos_model import ConfiguracionContactos
from app.core.database.tenant_repository import TenantScopedRepository


class ConfiguracionContactosRepository(TenantScopedRepository[ConfiguracionContactos]):
    model = ConfiguracionContactos

    async def obtener(self) -> ConfiguracionContactos | None:
        resultado = await self.session.execute(self.scoped())
        return resultado.scalars().first()
