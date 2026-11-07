"""Recarga de saldo utilizable (SMS/RCS).
Tres medios, siempre pagos sueltos -- nunca recurrentes (confirmado contra la
doc real de Wompi: PSE exige redirección y Nequi aprobación por notificación
push en cada cobro, ninguno sirve para suscripción): tarjeta (tokeniza una
fuente simple, sin preautorización), PSE (requiere banco elegido por el
usuario) y Nequi (requiere su celular registrado).

Cada recarga queda `pendiente` hasta que el webhook la confirma -- igual que
onboarding y suscripción, nunca por la respuesta inmediata de la pasarela."""

import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas.sesion_schema import SesionUsuario
from app.billing.clients.wompi_client import PASARELA, WompiClient
from app.billing.enums.billing_enums import (
    ConceptoMovimientoSaldo,
    EstadoFuenteDePago,
    EstadoTransaccionPago,
    MedioRecarga,
    TipoFuenteDePago,
)
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.models.movimiento_saldo_model import MovimientoSaldo
from app.billing.repositories.fuente_de_pago_repository import FuenteDePagoRepository
from app.billing.repositories.movimiento_saldo_repository import (
    MovimientoSaldoRepository,
)

_DESCRIPCION_PAGO = "Recarga de saldo Pulso"


class MovimientoSaldoNoEncontradoError(ValueError):
    pass


class MovimientoSaldoService:
    def __init__(self, session: AsyncSession, wompi_client: WompiClient):
        self.session = session
        self.repository = MovimientoSaldoRepository(session)
        self.fuente_repository = FuenteDePagoRepository(session)
        self.wompi_client = wompi_client

    async def _crear_movimiento_pendiente(
        self, sesion: SesionUsuario, medio: MedioRecarga, monto_cop: int, prefijo: str
    ) -> MovimientoSaldo:
        referencia = f"{prefijo}-{sesion.tenant_id}-{uuid.uuid4().hex[:12]}"
        movimiento = await self.repository.add(
            MovimientoSaldo(
                tenant_id=sesion.tenant_id,
                concepto=ConceptoMovimientoSaldo.recarga,
                medio=medio,
                monto_cop=Decimal(monto_cop),
                estado=EstadoTransaccionPago.pendiente,
                referencia=referencia,
                id_externo_transaccion=None,
            )
        )
        await self.session.commit()
        return movimiento

    async def _finalizar(
        self, movimiento: MovimientoSaldo, transaccion: dict[str, Any] | None
    ) -> MovimientoSaldo:
        if transaccion is None:
            movimiento.estado = EstadoTransaccionPago.error
        else:
            movimiento.id_externo_transaccion = str(transaccion["data"]["id"])
        movimiento = await self.repository.update(movimiento)
        await self.session.commit()
        return movimiento

    async def recargar_tarjeta(
        self,
        sesion: SesionUsuario,
        monto_cop: int,
        token: str,
        acceptance_token: str,
        accept_personal_auth: str,
    ) -> MovimientoSaldo:
        movimiento = await self._crear_movimiento_pendiente(
            sesion, MedioRecarga.tarjeta, monto_cop, "recarga-tarjeta"
        )
        fuente_resp = await self.wompi_client.crear_fuente_de_pago(
            tipo="CARD",
            token=token,
            customer_email=sesion.email,
            acceptance_token=acceptance_token,
            accept_personal_auth=accept_personal_auth,
        )
        id_fuente_externo = str(fuente_resp["data"]["id"])
        await self.fuente_repository.add(
            FuenteDePago(
                tenant_id=sesion.tenant_id,
                tipo=TipoFuenteDePago.tarjeta,
                pasarela=PASARELA,
                id_externo=id_fuente_externo,
                estado=EstadoFuenteDePago.disponible,
                es_recurrente=False,
                descripcion="Recarga de saldo",
            )
        )
        await self.session.commit()

        try:
            transaccion = await self.wompi_client.crear_transaccion(
                reference=movimiento.referencia,
                amount_in_cents=monto_cop * 100,
                currency="COP",
                customer_email=sesion.email,
                payment_source_id=int(id_fuente_externo),
            )
        except httpx.HTTPError:
            return await self._finalizar(movimiento, None)
        return await self._finalizar(movimiento, transaccion)

    async def _tokens_frescos(self) -> tuple[str, str]:
        """PSE y Nequi son transacciones de `payment_method` directo, no de
        `payment_source`: necesitan su propio par de tokens de aceptación,
        igual que la preautorización de la suscripción (ver
        `fuente_de_pago_service.py`)."""

        tokens = await self.wompi_client.obtener_tokens_de_aceptacion()
        return (
            tokens["data"]["presigned_acceptance"]["acceptance_token"],
            tokens["data"]["presigned_personal_data_auth"]["acceptance_token"],
        )

    async def recargar_pse(
        self,
        sesion: SesionUsuario,
        monto_cop: int,
        user_type: int,
        user_legal_id_type: str,
        user_legal_id: str,
        financial_institution_code: str,
    ) -> tuple[MovimientoSaldo, str | None]:
        """Devuelve el movimiento y, si Wompi lo da, la URL a la que redirigir
        al usuario para autenticar con su banco (`extra.async_payment_url`)."""

        movimiento = await self._crear_movimiento_pendiente(
            sesion, MedioRecarga.pse, monto_cop, "recarga-pse"
        )
        try:
            acceptance_token, accept_personal_auth = await self._tokens_frescos()
            transaccion = await self.wompi_client.crear_transaccion(
                reference=movimiento.referencia,
                amount_in_cents=monto_cop * 100,
                currency="COP",
                customer_email=sesion.email,
                acceptance_token=acceptance_token,
                accept_personal_auth=accept_personal_auth,
                payment_method={
                    "type": "PSE",
                    "user_type": user_type,
                    "user_legal_id_type": user_legal_id_type,
                    "user_legal_id": user_legal_id,
                    "financial_institution_code": financial_institution_code,
                    "payment_description": _DESCRIPCION_PAGO,
                },
            )
        except httpx.HTTPError:
            movimiento = await self._finalizar(movimiento, None)
            return movimiento, None

        movimiento = await self._finalizar(movimiento, transaccion)
        url = (
            transaccion.get("data", {})
            .get("payment_method", {})
            .get("extra", {})
            .get("async_payment_url")
        )
        return movimiento, url

    async def recargar_nequi(
        self, sesion: SesionUsuario, monto_cop: int, phone_number: str
    ) -> MovimientoSaldo:
        movimiento = await self._crear_movimiento_pendiente(
            sesion, MedioRecarga.nequi, monto_cop, "recarga-nequi"
        )
        try:
            acceptance_token, accept_personal_auth = await self._tokens_frescos()
            transaccion = await self.wompi_client.crear_transaccion(
                reference=movimiento.referencia,
                amount_in_cents=monto_cop * 100,
                currency="COP",
                customer_email=sesion.email,
                acceptance_token=acceptance_token,
                accept_personal_auth=accept_personal_auth,
                payment_method={"type": "NEQUI", "phone_number": phone_number},
            )
        except httpx.HTTPError:
            return await self._finalizar(movimiento, None)
        return await self._finalizar(movimiento, transaccion)

    async def consultar_estado_movimiento(self, public_id: UUID) -> MovimientoSaldo:
        movimiento = await self.repository.obtener_por_public_id(public_id)
        if movimiento is None:
            raise MovimientoSaldoNoEncontradoError("Movimiento de saldo no encontrado.")
        return movimiento

    async def listar_movimientos(self) -> list[MovimientoSaldo]:
        return await self.repository.listar_recientes()

    async def calcular_saldo(self) -> Decimal:
        return await self.repository.calcular_saldo_disponible()
