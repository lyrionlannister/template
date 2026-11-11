"""Cliente de Meta Cloud API (Graph API). Mismo patrón que
`billing/clients/wompi_client.py`: cliente httpx reusable, sin
reintentos, `raise_for_status`, secretos leídos frescos de `get_settings()`
en cada llamada.

Contrato verificado contra la documentación oficial de Meta
(developers.facebook.com/docs/graph-api, /docs/whatsapp/cloud-api) el
2026-11-10:

- Intercambio de código de Embedded Signup: `GET /oauth/access_token` con
  `client_id`/`client_secret`/`code`.
- Envío de plantilla: `POST /{phone_number_id}/messages`, con
  `Authorization: Bearer <token>`. Los parámetros del cuerpo de la
  plantilla son SIEMPRE posicionales (`{{1}}`, `{{2}}`...), nunca por
  nombre -- Meta no soporta placeholders con nombre en `components`."""

from typing import Any

import httpx

from app.core.config.settings import get_settings


def _base_url() -> str:
    version = get_settings().messaging.meta_graph_api_version
    return f"https://graph.facebook.com/{version}"


class MetaClient:
    def __init__(self, cliente_http: httpx.AsyncClient | None = None):
        self._cliente_propio = cliente_http is None
        self._http = cliente_http or httpx.AsyncClient(
            base_url=_base_url(), timeout=15.0
        )

    async def cerrar(self) -> None:
        if self._cliente_propio:
            await self._http.aclose()

    async def intercambiar_code_por_token(self, code: str) -> dict[str, Any]:
        settings = get_settings().messaging
        respuesta = await self._http.get(
            "/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret.get_secret_value(),
                "code": code,
            },
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_numero_telefono(
        self, phone_number_id: str, token_acceso: str
    ) -> str:
        """El flujo de Embedded Signup entrega `waba_id`/`phone_number_id`
        por `postMessage`, pero no el número en formato legible -- hay que
        pedirlo a Graph API ya con el token recién canjeado."""

        respuesta = await self._http.get(
            f"/{phone_number_id}",
            params={"fields": "display_phone_number"},
            headers={"Authorization": f"Bearer {token_acceso}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()["display_phone_number"]

    async def enviar_plantilla(
        self,
        *,
        phone_number_id: str,
        token_acceso: str,
        telefono_destino: str,
        nombre_plantilla: str,
        idioma: str,
        parametros_posicionales: list[str],
    ) -> dict[str, Any]:
        componentes = []
        if parametros_posicionales:
            componentes.append(
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": valor}
                        for valor in parametros_posicionales
                    ],
                }
            )
        cuerpo = {
            "messaging_product": "whatsapp",
            "to": telefono_destino,
            "type": "template",
            "template": {
                "name": nombre_plantilla,
                "language": {"code": idioma},
                "components": componentes,
            },
        }
        respuesta = await self._http.post(
            f"/{phone_number_id}/messages",
            json=cuerpo,
            headers={"Authorization": f"Bearer {token_acceso}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def crear_plantilla_autenticacion(
        self,
        *,
        waba_id: str,
        token_acceso: str,
        nombre: str,
        idioma: str,
        expiracion_minutos: int,
    ) -> dict[str, Any]:
        """`POST /{waba_id}/message_templates`, `category: AUTHENTICATION`.
        Meta no deja personalizar el texto de una plantilla de autenticación
        más allá de estos parámetros: lo genera ella misma a partir de los
        componentes (cuerpo con recomendación de seguridad, pie con minutos
        de expiración, botón de copiar código)."""

        cuerpo = {
            "name": nombre,
            "language": idioma,
            "category": "AUTHENTICATION",
            "components": [
                {"type": "BODY", "add_security_recommendation": True},
                {"type": "FOOTER", "code_expiration_minutes": expiracion_minutos},
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {"type": "OTP", "otp_type": "COPY_CODE", "text": "Copiar código"}
                    ],
                },
            ],
        }
        respuesta = await self._http.post(
            f"/{waba_id}/message_templates",
            json=cuerpo,
            headers={"Authorization": f"Bearer {token_acceso}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_estado_plantilla(
        self, *, meta_template_id: str, token_acceso: str
    ) -> str:
        respuesta = await self._http.get(
            f"/{meta_template_id}",
            params={"fields": "status"},
            headers={"Authorization": f"Bearer {token_acceso}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()["status"]
