"""Tests del cliente Sent.dm: SDK oficial `sentdm` simulado, sin red real.
Cubre el invariante "WhatsApp nunca por Sent.dm" en el propio cliente -- ver
"Garantía: WhatsApp nunca por Sent.dm" en api/CLAUDE.md."""

import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.messaging.clients.sent_client import SentClient
from app.messaging.exceptions import CanalNoPermitidoEnSentError


class _RespuestaFalsa:
    def __init__(self, datos: dict):
        self._datos = datos

    def model_dump(self) -> dict:
        return self._datos


class _MessagesFalso:
    def __init__(self):
        self.llamado_con: dict | None = None

    async def send(self, *, to, channel, template):
        self.llamado_con = {"to": to, "channel": channel, "template": template}
        return _RespuestaFalsa({"data": {"status": "QUEUED"}})


class _AsyncSentFalso:
    def __init__(self):
        self.messages = _MessagesFalso()
        self.cerrado = False

    async def close(self):
        self.cerrado = True


@pytest.mark.parametrize("canal", [CanalMensajeria.sms, CanalMensajeria.rcs])
@pytest.mark.asyncio
async def test_enviar_plantilla_arma_el_body_con_el_canal_fijado(canal):
    sdk_falso = _AsyncSentFalso()
    cliente = SentClient(cliente=sdk_falso)

    resultado = await cliente.enviar_plantilla(
        canal=canal,
        telefono_destino="+573001234567",
        nombre_plantilla="recordatorio_pago",
        parametros={"nombre": "Ana"},
    )

    assert resultado["data"]["status"] == "QUEUED"
    llamada = sdk_falso.messages.llamado_con
    assert llamada["to"] == ["+573001234567"]
    assert llamada["channel"] == [canal.value]
    assert llamada["template"] == {
        "name": "recordatorio_pago",
        "parameters": {"nombre": "Ana"},
    }
    # Nunca se construye con texto libre: siempre template, nunca "text".
    assert "text" not in llamada["template"]


@pytest.mark.asyncio
async def test_canal_whatsapp_se_rechaza_antes_de_llamar_a_sent():
    sdk_falso = _AsyncSentFalso()
    cliente = SentClient(cliente=sdk_falso)

    with pytest.raises(CanalNoPermitidoEnSentError):
        await cliente.enviar_plantilla(
            canal=CanalMensajeria.whatsapp,
            telefono_destino="+573001234567",
            nombre_plantilla="x",
            parametros={},
        )
    assert sdk_falso.messages.llamado_con is None


@pytest.mark.asyncio
async def test_cerrar_cierra_el_cliente_del_sdk():
    sdk_falso = _AsyncSentFalso()
    cliente = SentClient(cliente=sdk_falso)

    await cliente.cerrar()

    assert sdk_falso.cerrado is True
