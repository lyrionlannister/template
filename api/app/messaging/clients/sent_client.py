"""Cliente de Sent.dm. Usa el SDK oficial `sentdm` (import `sent_dm`,
`AsyncSent`), no httpx crudo -- a diferencia de `meta_client.py`, que sí usa
httpx crudo porque Meta no publica SDK oficial de WhatsApp Cloud API.

Contrato verificado contra docs.sent.dm y github.com/sentdm/sent-dm-python
el 2026-11-11:

- `client.messages.send(to=[...], channel=[...], template={"name", "parameters"})`.
  `template` acepta `id`/`name` + `parameters` (objeto nombrado) o, en su
  lugar, `text` libre. Texto libre no sirve para el primer contacto con
  alguien que nunca respondió -- Pulso siempre usa `template`.
- Canal explícito por petición, nunca una lista construida por el llamador:
  este cliente solo acepta `sms` o `rcs`. Si recibe `whatsapp`, falla antes
  de construir la petición -- ver "Garantía: WhatsApp nunca por Sent.dm" en
  api/CLAUDE.md. Este archivo no debe ganar nunca un valor ni una rama que
  mencione whatsapp."""

from typing import Any

from sent_dm import AsyncSent

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.core.config.settings import get_settings
from app.messaging.exceptions import CanalNoPermitidoEnSentError

_CANALES_PERMITIDOS = {CanalMensajeria.sms, CanalMensajeria.rcs}


class SentClient:
    def __init__(self, cliente: AsyncSent | None = None):
        settings = get_settings().messaging
        self._client = cliente or AsyncSent(
            api_key=settings.sentdm_api_key.get_secret_value(),
            base_url=settings.sentdm_base_url,
        )

    async def cerrar(self) -> None:
        await self._client.close()

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
        respuesta = await self._client.messages.send(
            to=[telefono_destino],
            channel=[canal.value],
            template={"name": nombre_plantilla, "parameters": parametros},
        )
        return respuesta.model_dump()
