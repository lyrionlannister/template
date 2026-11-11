"""Cliente de Sent.dm (API v3). Mismo patrón que `meta_client.py`: cliente
httpx reusable, sin reintentos, `raise_for_status`, secretos leídos frescos
de `get_settings()` en cada llamada.

Contrato verificado contra docs.sent.dm el 2026-11-11:

- `POST /v3/messages`, header `x-api-key`, body con `to` (lista),
  `channel` (lista) y exactamente uno de `template` (`id`/`name` +
  `parameters`, objeto nombrado) o `text` (texto libre). Texto libre no
  sirve para el primer contacto con alguien que nunca respondió -- Pulso
  siempre usa `template`.
- Canal explícito por petición, nunca una lista construida por el llamador:
  este cliente solo acepta `sms` o `rcs`. Si recibe `whatsapp`, falla antes
  de construir la petición -- ver "Garantía: WhatsApp nunca por Sent.dm" en
  api/CLAUDE.md. Este archivo no debe ganar nunca un valor ni una rama que
  mencione whatsapp."""

from typing import Any

import httpx

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.core.config.settings import get_settings
from app.messaging.exceptions import CanalNoPermitidoEnSentError

_CANALES_PERMITIDOS = {CanalMensajeria.sms, CanalMensajeria.rcs}


class SentClient:
    def __init__(self, cliente_http: httpx.AsyncClient | None = None):
        self._cliente_propio = cliente_http is None
        self._http = cliente_http or httpx.AsyncClient(
            base_url=get_settings().messaging.sentdm_base_url, timeout=15.0
        )

    async def cerrar(self) -> None:
        if self._cliente_propio:
            await self._http.aclose()

    async def enviar_plantilla(
        self,
        *,
        canal: CanalMensajeria,
        telefono_destino: str,
        nombre_plantilla: str,
        parametros: dict[str, str],
    ) -> dict[str, Any]:
        if canal not in _CANALES_PERMITIDOS:
            raise CanalNoPermitidoEnSentError(
                f"Sent.dm no envía el canal {canal.value}. Permitidos: "
                f"{', '.join(c.value for c in _CANALES_PERMITIDOS)}."
            )
        settings = get_settings().messaging
        cuerpo = {
            "to": [telefono_destino],
            "channel": [canal.value],
            "template": {"name": nombre_plantilla, "parameters": parametros},
        }
        respuesta = await self._http.post(
            "/v3/messages",
            json=cuerpo,
            headers={"x-api-key": settings.sentdm_api_key.get_secret_value()},
        )
        respuesta.raise_for_status()
        return respuesta.json()
