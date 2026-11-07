"""Acceso a datos de `CodigoOtp`. `verificar_con_excepciones` es el único
punto de lectura que decide si un código es válido."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.auth.enums.auth_enums import CanalOtp
from app.auth.exceptions import (
    CodigoOtpExpiradoError,
    CodigoOtpNoEncontradoError,
    CodigoOtpYaUsadoError,
)
from app.auth.models.codigo_otp_model import CodigoOtp
from app.core.database.tenant_repository import TenantScopedRepository


class CodigoOtpRepository(TenantScopedRepository[CodigoOtp]):
    model = CodigoOtp

    async def verificar_con_excepciones(
        self, usuario_id: int, codigo_hash: str, canal: CanalOtp
    ) -> CodigoOtp:
        resultado = await self.session.execute(
            select(CodigoOtp).where(
                CodigoOtp.usuario_id == usuario_id,
                CodigoOtp.codigo_hash == codigo_hash,
                CodigoOtp.canal == canal,
            )
        )
        registro = resultado.scalars().first()

        if registro is None:
            raise CodigoOtpNoEncontradoError("Código incorrecto.")
        if registro.consumido_en is not None:
            raise CodigoOtpYaUsadoError("El código ya fue utilizado.")
        if registro.expira_en <= datetime.now(UTC):
            raise CodigoOtpExpiradoError("El código expiró.")
        return registro

    async def marcar_consumido(self, registro: CodigoOtp) -> CodigoOtp:
        registro.consumido_en = datetime.now(UTC)
        return await self.update(registro)
