"""Plantilla de autenticación de WhatsApp de PLATAFORMA (OTP de login):
se crea desde el panel de administrador del sistema, queda en revisión de
Meta, y el panel la sincroniza hasta que quede aprobada."""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import get_settings
from app.messaging.clients.meta_client import MetaClient
from app.messaging.exceptions import PlantillaOtpPlataformaNoEncontradaError
from app.messaging.models.plantilla_otp_plataforma_model import PlantillaOtpPlataforma

EXPIRACION_OTP_MINUTOS = 5
_NO_ALFANUMERICO = re.compile(r"[^a-z0-9_]+")


def _normalizar_nombre(nombre: str) -> str:
    return _NO_ALFANUMERICO.sub("_", nombre.strip().lower())


class PlantillaOtpPlataformaService:
    def __init__(self, session: AsyncSession, meta_client: MetaClient):
        self.session = session
        self.meta_client = meta_client

    async def crear(self, nombre: str, idioma: str) -> PlantillaOtpPlataforma:
        nombre_normalizado = _normalizar_nombre(nombre)
        s = get_settings().messaging
        respuesta = await self.meta_client.crear_plantilla_autenticacion(
            waba_id=s.meta_platform_waba_id,
            token_acceso=s.meta_access_token.get_secret_value(),
            nombre=nombre_normalizado,
            idioma=idioma,
            expiracion_minutos=EXPIRACION_OTP_MINUTOS,
        )
        plantilla = PlantillaOtpPlataforma(
            nombre=nombre_normalizado,
            idioma=idioma,
            estado_meta="PENDING",
            meta_template_id=str(respuesta["id"]),
        )
        self.session.add(plantilla)
        await self.session.flush()
        await self.session.refresh(plantilla)
        await self.session.commit()
        return plantilla

    async def obtener(self, public_id: UUID) -> PlantillaOtpPlataforma:
        resultado = await self.session.execute(
            select(PlantillaOtpPlataforma).where(
                PlantillaOtpPlataforma.public_id == public_id
            )
        )
        plantilla = resultado.scalars().first()
        if plantilla is None:
            raise PlantillaOtpPlataformaNoEncontradaError(
                "La plantilla de OTP de plataforma no existe."
            )
        return plantilla

    async def listar(self) -> list[PlantillaOtpPlataforma]:
        resultado = await self.session.execute(
            select(PlantillaOtpPlataforma).order_by(
                PlantillaOtpPlataforma.creado_en.desc()
            )
        )
        return list(resultado.scalars().all())

    async def sincronizar_estado(self, public_id: UUID) -> PlantillaOtpPlataforma:
        plantilla = await self.obtener(public_id)
        s = get_settings().messaging
        estado = await self.meta_client.obtener_estado_plantilla(
            meta_template_id=plantilla.meta_template_id,
            token_acceso=s.meta_access_token.get_secret_value(),
        )
        plantilla.estado_meta = estado
        await self.session.flush()
        await self.session.refresh(plantilla)
        await self.session.commit()
        return plantilla

    async def obtener_aprobada(self) -> PlantillaOtpPlataforma | None:
        resultado = await self.session.execute(
            select(PlantillaOtpPlataforma)
            .where(PlantillaOtpPlataforma.estado_meta == "APPROVED")
            .order_by(PlantillaOtpPlataforma.creado_en.desc())
        )
        return resultado.scalars().first()
