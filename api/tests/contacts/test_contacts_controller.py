"""Criterio de aceptación de la Tarea 3: el endpoint de previsualización
delega 100% en `ContactsService` -- aquí solo se prueba que la sesión real
(cookie, no mock) llega con su `tenant_id` y que la respuesta serializa en
camelCase."""

import io
import re
import uuid

import openpyxl
import polars as pl
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update

from app.app_platform.models.plan_model import Plan
from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"


def _email_de_prueba() -> str:
    return f"test-contactos-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


def _usuario_id_desde_cookie(cliente: AsyncClient) -> int:
    from app.core.security.token_service import TokenService

    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


def _extraer_codigo_otp(salida: str) -> str:
    coincidencia = re.search(r"codigo=(\d{6})", salida)
    assert coincidencia, f"no se encontró el código OTP en la salida: {salida!r}"
    return coincidencia.group(1)


async def _registrar_y_verificar_mfa(cliente: AsyncClient, email: str, capsys) -> int:
    respuesta = await cliente.post(
        "/auth/registro",
        json={
            "nombreOrganizacion": "Empresa de prueba contactos",
            "email": email,
            "password": _PASSWORD,
        },
    )
    assert respuesta.status_code == 201
    usuario_id = _usuario_id_desde_cookie(cliente)

    await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
    codigo = _extraer_codigo_otp(capsys.readouterr().out)
    await cliente.post(
        "/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"}
    )
    return usuario_id


async def _limpiar(email: str, usuario_id: int | None) -> None:
    async with async_session_factory() as session:
        if usuario_id is not None:
            await session.execute(
                delete(CodigoOtp).where(CodigoOtp.usuario_id == usuario_id)
            )
            resultado = await session.execute(
                delete(Usuario)
                .where(Usuario.id == usuario_id)
                .returning(Usuario.tenant_id)
            )
            tenant_id = resultado.scalar_one_or_none()
            if tenant_id is not None:
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    await valkey_client.delete(f"login-fail:{email}")


async def test_previsualizar_csv_exitoso_devuelve_columnas_y_preview_id(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.csv",
                    b"telefono,nombre\n+573001112233,Ana\n",
                    "text/csv",
                )
            },
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["columnas"] == ["telefono", "nombre"]
        assert cuerpo["totalFilas"] == 1
        assert cuerpo["muestra"] == [{"telefono": "+573001112233", "nombre": "Ana"}]
        assert cuerpo["previewId"]

        patron = f"importacion:preview:*:{cuerpo['previewId']}"
        async for clave in valkey_client.scan_iter(match=patron):
            await valkey_client.delete(clave)
    finally:
        await _limpiar(email, usuario_id)


async def test_previsualizar_xlsx_exitoso_devuelve_columnas_y_preview_id(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        libro = openpyxl.Workbook()
        hoja = libro.active
        hoja.append(["telefono", "nombre"])
        hoja.append(["+573001112233", "Ana"])
        buffer = io.BytesIO()
        libro.save(buffer)

        respuesta = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.xlsx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["columnas"] == ["telefono", "nombre"]
        assert cuerpo["totalFilas"] == 1

        patron = f"importacion:preview:*:{cuerpo['previewId']}"
        async for clave in valkey_client.scan_iter(match=patron):
            await valkey_client.delete(clave)
    finally:
        await _limpiar(email, usuario_id)


async def test_previsualizar_parquet_exitoso_devuelve_columnas_y_preview_id(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        df = pl.DataFrame({"telefono": ["+573001112233"], "nombre": ["Ana"]})
        buffer = io.BytesIO()
        df.write_parquet(buffer)

        respuesta = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.parquet",
                    buffer.getvalue(),
                    "application/octet-stream",
                )
            },
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["columnas"] == ["telefono", "nombre"]
        assert cuerpo["totalFilas"] == 1

        patron = f"importacion:preview:*:{cuerpo['previewId']}"
        async for clave in valkey_client.scan_iter(match=patron):
            await valkey_client.delete(clave)
    finally:
        await _limpiar(email, usuario_id)


async def test_previsualizar_rechaza_archivo_que_excede_limite_del_plan_sin_cachear(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    plan_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        async with async_session_factory() as session:
            plan_minimo = Plan(
                nombre=f"plan-prueba-limite-{uuid.uuid4().hex[:8]}",
                precio_mensual_cop=100_000,
                limite_filas_importacion=1,
                mensajes_marketing_incluidos=1000,
                precio_marketing_mensaje_cop=90,
                precio_utility_mensaje_cop=15,
                max_usuarios=1,
                max_whatsapp_numeros=1,
            )
            session.add(plan_minimo)
            await session.flush()
            plan_id = plan_minimo.id

            resultado = await session.execute(
                select(Usuario.tenant_id).where(Usuario.id == usuario_id)
            )
            tenant_id = resultado.scalar_one()
            await session.execute(
                update(Tenant).where(Tenant.id == tenant_id).values(plan_id=plan_id)
            )
            await session.commit()

        contenido = "telefono\n" + "\n".join(f"+57300000{i:04d}" for i in range(2))
        patron_cache = f"importacion:preview:{tenant_id}:*"

        respuesta = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={"archivo": ("contactos.csv", contenido.encode("utf-8"), "text/csv")},
        )

        assert respuesta.status_code == 422, respuesta.text
        claves = [clave async for clave in valkey_client.scan_iter(match=patron_cache)]
        assert claves == []
    finally:
        await _limpiar(email, usuario_id)
        if plan_id is not None:
            async with async_session_factory() as session:
                await session.execute(delete(Plan).where(Plan.id == plan_id))
                await session.commit()


async def test_confirmar_importacion_crea_registro_y_borra_el_preview(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        previsualizacion = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.csv",
                    b"telefono,nombre\n+573001112233,Ana\n",
                    "text/csv",
                )
            },
        )
        preview_id = previsualizacion.json()["previewId"]

        respuesta = await cliente.post(
            "/contacts/importaciones",
            json={
                "previewId": preview_id,
                "columnaTelefono": "telefono",
                "mapeoVariables": {"nombre": "nombre"},
            },
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["estado"] == "pendiente"
        assert cuerpo["totalFilas"] == 1
        assert cuerpo["publicId"]

        segunda_confirmacion = await cliente.post(
            "/contacts/importaciones",
            json={
                "previewId": preview_id,
                "columnaTelefono": "telefono",
                "mapeoVariables": {"nombre": "nombre"},
            },
        )
        assert segunda_confirmacion.status_code == 404, segunda_confirmacion.text
    finally:
        await _limpiar(email, usuario_id)


async def test_confirmar_importacion_rechaza_columna_telefono_inexistente(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        previsualizacion = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.csv",
                    b"telefono,nombre\n+573001112233,Ana\n",
                    "text/csv",
                )
            },
        )
        preview_id = previsualizacion.json()["previewId"]

        respuesta = await cliente.post(
            "/contacts/importaciones",
            json={
                "previewId": preview_id,
                "columnaTelefono": "columna_que_no_existe",
                "mapeoVariables": {"nombre": "nombre"},
            },
        )

        assert respuesta.status_code == 400, respuesta.text
    finally:
        await _limpiar(email, usuario_id)


async def test_estado_y_rechazos_de_importacion_tras_procesarse(
    cliente: AsyncClient, capsys
) -> None:
    """El `BackgroundTask` corre dentro de la misma llamada ASGI (no hay
    loop de servidor real en el test), así que para cuando el cliente
    recibe la respuesta del `GET` el procesamiento ya terminó."""

    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        contenido = b"telefono,nombre\n+573001112233,Ana\nnumero-invalido,Luis\n"
        previsualizacion = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={"archivo": ("contactos.csv", contenido, "text/csv")},
        )
        preview_id = previsualizacion.json()["previewId"]

        confirmacion = await cliente.post(
            "/contacts/importaciones",
            json={
                "previewId": preview_id,
                "columnaTelefono": "telefono",
                "mapeoVariables": {"nombre": "nombre"},
            },
        )
        importacion_public_id = confirmacion.json()["publicId"]

        estado = await cliente.get(f"/contacts/importaciones/{importacion_public_id}")
        assert estado.status_code == 200, estado.text
        cuerpo_estado = estado.json()
        assert cuerpo_estado["estado"] == "completada"
        assert cuerpo_estado["filasAceptadas"] == 1
        assert cuerpo_estado["filasRechazadas"] == 1

        rechazos = await cliente.get(
            f"/contacts/importaciones/{importacion_public_id}/rechazos"
        )
        assert rechazos.status_code == 200, rechazos.text
        cuerpo_rechazos = rechazos.json()
        assert cuerpo_rechazos["total"] == 1
        assert cuerpo_rechazos["rechazos"][0]["filaCruda"]["telefono"] == (
            "numero-invalido"
        )
    finally:
        await _limpiar(email, usuario_id)


async def test_estado_de_importacion_inexistente_da_404(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta = await cliente.get(f"/contacts/importaciones/{uuid.uuid4()}")
        assert respuesta.status_code == 404, respuesta.text
    finally:
        await _limpiar(email, usuario_id)


async def test_previsualizar_rechaza_formato_no_soportado(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta = await cliente.post(
            "/contacts/importaciones/previsualizar",
            files={
                "archivo": (
                    "contactos.txt",
                    b"telefono,nombre\n+573001112233,Ana\n",
                    "text/plain",
                )
            },
        )

        assert respuesta.status_code == 400, respuesta.text
    finally:
        await _limpiar(email, usuario_id)
