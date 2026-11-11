"""Tests del cliente Meta Cloud API: transporte simulado, sin red real."""

import json

import httpx
import pytest

from app.messaging.clients.meta_client import MetaClient


@pytest.mark.asyncio
async def test_intercambiar_code_por_token_envia_client_id_y_secret():
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["params"] = dict(request.url.params)
        return httpx.Response(200, json={"access_token": "tok-123"})

    cliente = MetaClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://graph.facebook.com/v27.0",
        )
    )
    resultado = await cliente.intercambiar_code_por_token("code-abc")

    assert resultado["access_token"] == "tok-123"
    assert capturado["params"]["code"] == "code-abc"
    assert "client_id" in capturado["params"]
    assert "client_secret" in capturado["params"]


@pytest.mark.asyncio
async def test_enviar_plantilla_usa_parametros_posicionales_en_orden():
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["headers"] = request.headers
        capturado["body"] = json.loads(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.123"}]})

    cliente = MetaClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://graph.facebook.com/v27.0",
        )
    )
    resultado = await cliente.enviar_plantilla(
        phone_number_id="123",
        token_acceso="tok-xyz",
        telefono_destino="+573001234567",
        nombre_plantilla="bienvenida",
        idioma="es_CO",
        parametros_posicionales=["Ana", "100000"],
    )

    assert resultado["messages"][0]["id"] == "wamid.123"
    assert capturado["headers"]["authorization"] == "Bearer tok-xyz"
    componentes = capturado["body"]["template"]["components"]
    assert componentes[0]["type"] == "body"
    assert componentes[0]["parameters"] == [
        {"type": "text", "text": "Ana"},
        {"type": "text", "text": "100000"},
    ]
    # Nunca por nombre: ninguna clave de variable aparece en el payload.
    assert "nombre" not in json.dumps(componentes)


@pytest.mark.asyncio
async def test_crear_plantilla_autenticacion_arma_los_componentes_fijos():
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["headers"] = request.headers
        capturado["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "tpl-1", "status": "PENDING"})

    cliente = MetaClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://graph.facebook.com/v27.0",
        )
    )
    resultado = await cliente.crear_plantilla_autenticacion(
        waba_id="waba-1",
        token_acceso="tok-xyz",
        nombre="pulso_otp",
        idioma="es",
        expiracion_minutos=5,
    )

    assert resultado["id"] == "tpl-1"
    assert capturado["headers"]["authorization"] == "Bearer tok-xyz"
    cuerpo = capturado["body"]
    assert cuerpo["category"] == "AUTHENTICATION"
    assert cuerpo["language"] == "es"
    tipos = {c["type"] for c in cuerpo["components"]}
    assert tipos == {"BODY", "FOOTER", "BUTTONS"}
    footer = next(c for c in cuerpo["components"] if c["type"] == "FOOTER")
    assert footer["code_expiration_minutes"] == 5
    botones = next(c for c in cuerpo["components"] if c["type"] == "BUTTONS")
    assert botones["buttons"][0]["otp_type"] == "COPY_CODE"


@pytest.mark.asyncio
async def test_obtener_estado_plantilla_lee_el_status():
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "APPROVED"})

    cliente = MetaClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://graph.facebook.com/v27.0",
        )
    )
    estado = await cliente.obtener_estado_plantilla(
        meta_template_id="tpl-1", token_acceso="tok-xyz"
    )
    assert estado == "APPROVED"


@pytest.mark.asyncio
async def test_obtener_numero_telefono_lee_display_phone_number():
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"display_phone_number": "+52 1 833 289 1881"})

    cliente = MetaClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://graph.facebook.com/v27.0",
        )
    )
    numero = await cliente.obtener_numero_telefono("123", "tok-xyz")
    assert numero == "+52 1 833 289 1881"
