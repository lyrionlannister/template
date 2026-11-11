"""`PlantillaOtpPlataformaService` contra la base real, con `MetaClient`
reemplazado por un doble -- no hay red real ni dependencia de que Meta
apruebe nada en un test."""

import pytest
from sqlalchemy import delete

from app.core.database.session import async_session_factory
from app.messaging.models.plantilla_otp_plataforma_model import PlantillaOtpPlataforma
from app.messaging.services.plantilla_otp_plataforma_service import (
    PlantillaOtpPlataformaService,
)


@pytest.fixture(autouse=True)
async def _limpiar_plantillas_otp_plataforma():
    yield
    async with async_session_factory() as session:
        await session.execute(delete(PlantillaOtpPlataforma))
        await session.commit()


class _MetaClientFalso:
    def __init__(self):
        self.ultima_creacion: dict | None = None

    async def crear_plantilla_autenticacion(self, **kwargs) -> dict:
        self.ultima_creacion = kwargs
        return {"id": "tpl-falso-1", "status": "PENDING"}

    async def obtener_estado_plantilla(self, **kwargs) -> str:
        return "APPROVED"


async def test_crear_normaliza_el_nombre_y_persiste_pendiente():
    meta_falso = _MetaClientFalso()
    async with async_session_factory() as session:
        servicio = PlantillaOtpPlataformaService(session, meta_falso)
        plantilla = await servicio.crear("Pulso OTP", "es")

    assert plantilla.nombre == "pulso_otp"
    assert plantilla.estado_meta == "PENDING"
    assert plantilla.meta_template_id == "tpl-falso-1"
    assert meta_falso.ultima_creacion["nombre"] == "pulso_otp"


async def test_sincronizar_estado_actualiza_desde_meta():
    meta_falso = _MetaClientFalso()
    async with async_session_factory() as session:
        servicio = PlantillaOtpPlataformaService(session, meta_falso)
        plantilla = await servicio.crear("pulso_otp_sync", "es")
        actualizada = await servicio.sincronizar_estado(plantilla.public_id)

    assert actualizada.estado_meta == "APPROVED"


async def test_obtener_aprobada_devuelve_none_si_ninguna_lo_esta():
    meta_falso = _MetaClientFalso()
    async with async_session_factory() as session:
        servicio = PlantillaOtpPlataformaService(session, meta_falso)
        await servicio.crear("pulso_otp_pendiente", "es")
        aprobada = await servicio.obtener_aprobada()

    assert aprobada is None


async def test_obtener_aprobada_devuelve_la_que_ya_fue_sincronizada():
    meta_falso = _MetaClientFalso()
    async with async_session_factory() as session:
        servicio = PlantillaOtpPlataformaService(session, meta_falso)
        plantilla = await servicio.crear("pulso_otp_aprobada", "es")
        await servicio.sincronizar_estado(plantilla.public_id)
        aprobada = await servicio.obtener_aprobada()

    assert aprobada is not None
    assert aprobada.public_id == plantilla.public_id
