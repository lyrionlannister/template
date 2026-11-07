"""Pool mensual de mensajes de WhatsApp incluidos en la suscripción
(`/CLAUDE.md`, «Mensajes incluidos en la suscripción»).

Solo WhatsApp marketing y utility lo tocan — utility a 1/16 de un crédito
de marketing. SMS, RCS y las categorías authentication/service de WhatsApp
nunca lo descuentan, `consumir()` es un no-op para ellos.

Vive en Valkey, con la clave calificada por mes (`pool:{tenant_id}:{aaaa-mm}`):
no se acumula entre meses porque cada mes es literalmente otra clave, sin
necesidad de un job de reinicio. La unidad atómica es 1/16 de mensaje de
marketing (un entero: marketing consume 16, utility consume 1) para no
tocar `Decimal`/`float` en este conteo.
"""

from datetime import date

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.models.plan_model import Plan
from app.core.valkey.client import valkey_client

UNIDADES_POR_MENSAJE_MARKETING = 16
UNIDADES_POR_MENSAJE_UTILITY = 1


def _unidades_por_mensaje(categoria: CategoriaMensaje) -> int | None:
    if categoria == CategoriaMensaje.marketing:
        return UNIDADES_POR_MENSAJE_MARKETING
    if categoria == CategoriaMensaje.utility:
        return UNIDADES_POR_MENSAJE_UTILITY
    return None


class PoolIncluidosService:
    def _clave(self, tenant_id: int, mes: str) -> str:
        return f"pool:{tenant_id}:{mes}"

    def _mes_actual(self) -> str:
        return date.today().strftime("%Y-%m")

    async def unidades_consumidas(self, tenant_id: int, mes: str | None = None) -> int:
        crudo = await valkey_client.get(
            self._clave(tenant_id, mes or self._mes_actual())
        )
        return int(crudo) if crudo is not None else 0

    async def unidades_disponibles(
        self, tenant_id: int, plan: Plan, mes: str | None = None
    ) -> int:
        incluidas = plan.mensajes_marketing_incluidos * UNIDADES_POR_MENSAJE_MARKETING
        consumidas = await self.unidades_consumidas(tenant_id, mes)
        return max(0, incluidas - consumidas)

    async def consumir(
        self,
        tenant_id: int,
        canal: CanalMensajeria,
        categoria: CategoriaMensaje | None,
        cantidad: int = 1,
    ) -> int:
        """Devuelve las unidades (1/16 de mensaje) efectivamente consumidas
        del pool. SMS/RCS y categorías de WhatsApp fuera de marketing/utility
        devuelven 0: nunca tocan el pool."""

        if canal != CanalMensajeria.whatsapp or categoria is None:
            return 0
        unidades_por_mensaje = _unidades_por_mensaje(categoria)
        if unidades_por_mensaje is None:
            return 0

        unidades = unidades_por_mensaje * cantidad
        await valkey_client.incrby(self._clave(tenant_id, self._mes_actual()), unidades)
        return unidades
