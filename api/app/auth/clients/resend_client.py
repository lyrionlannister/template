"""Cliente de envío de correo transaccional (hoy, únicamente Resend). Solo
este archivo sabe que el proveedor concreto es Resend.

Contrato verificado contra la documentación oficial (resend.com/docs, vía
Context7) el 2026-11-07, no inventado: `POST https://api.resend.com/emails`,
header `Authorization: Bearer <api key>`, cuerpo `{from, to, subject, html}`.
"""

import httpx

from app.core.config.settings import get_settings

_BASE_URL = "https://api.resend.com/emails"


async def enviar_email(
    *, destinatario: str, asunto: str, html: str, idempotency_key: str
) -> None:
    configuracion = get_settings().auth
    api_key = configuracion.resend_api_key.get_secret_value()
    remitente = configuracion.resend_from_email

    async with httpx.AsyncClient(timeout=10.0) as cliente:
        respuesta = await cliente.post(
            _BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Idempotency-Key": idempotency_key,
            },
            json={
                "from": remitente,
                "to": [destinatario],
                "subject": asunto,
                "html": html,
            },
        )
    respuesta.raise_for_status()
