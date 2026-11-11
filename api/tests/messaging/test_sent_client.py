"""Tests del cliente Sent.dm: transporte simulado, sin red real. Cubre el
invariante "WhatsApp nunca por Sent.dm" en el propio cliente -- ver
"Garantía: WhatsApp nunca por Sent.dm" en api/CLAUDE.md."""

import json

import httpx
import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.messaging.clients.sent_client import SentClient
from app.messaging.exceptions import CanalNoPermitidoEnSentError


@pytest.mark.parametrize("canal", [CanalMensajeria.sms, CanalMensajeria.rcs])
@pytest.mark.asyncio
async def test_enviar_plantilla_arma_el_body_con_el_canal_fijado(canal):
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["headers"] = request.headers
        capturado["body"] = json.loads(request.content)
        capturado["path"] = request.url.path
        return httpx.Response(202, json={"data": {"status": "QUEUED"}})

    cliente = SentClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler), base_url="https://api.sent.dm"
        )
    )
    resultado = await cliente.enviar_plantilla(
        canal=canal,
        telefono_destino="+573001234567",
        nombre_plantilla="recordatorio_pago",
        parametros={"nombre": "Ana"},
    )

    assert resultado["data"]["status"] == "QUEUED"
    assert capturado["path"] == "/v3/messages"
    assert "x-api-key" in capturado["headers"]
    assert capturado["body"]["to"] == ["+573001234567"]
    assert capturado["body"]["channel"] == [canal.value]
    assert capturado["body"]["template"] == {
        "name": "recordatorio_pago",
        "parameters": {"nombre": "Ana"},
    }
    # Nunca se construye con texto libre: siempre template, nunca "text".
    assert "text" not in capturado["body"]


@pytest.mark.asyncio
async def test_canal_whatsapp_se_rechaza_antes_de_llamar_a_sent():
    llamado = False

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal llamado
        llamado = True
        return httpx.Response(200, json={})

    cliente = SentClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler), base_url="https://api.sent.dm"
        )
    )
    with pytest.raises(CanalNoPermitidoEnSentError):
        await cliente.enviar_plantilla(
            canal=CanalMensajeria.whatsapp,
            telefono_destino="+573001234567",
            nombre_plantilla="x",
            parametros={},
        )
    assert llamado is False
