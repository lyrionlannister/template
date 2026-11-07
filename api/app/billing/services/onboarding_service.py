"""Pago único de onboarding. El cobro se confirma solo por webhook (ver
`evento_pago_service.py`): esta llamada deja el `Cobro` en `pendiente` y
devuelve ese estado, nunca marca el onboarding como pagado por la respuesta
inmediata de la pasarela."""

import uuid
from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.exceptions import ParametroComercialFaltanteError
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.auth.enums.auth_enums import RolUsuario
from app.auth.exceptions import PermisoInsuficienteError
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import PASARELA, WompiClient
from app.billing.enums.billing_enums import (
    ConceptoCobro,
    EstadoFuenteDePago,
    EstadoTransaccionPago,
    TipoFuenteDePago,
)
from app.billing.exceptions import OnboardingYaPagadoError
from app.billing.models.cobro_model import Cobro
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.repositories.cobro_repository import CobroRepository
from app.billing.repositories.fuente_de_pago_repository import FuenteDePagoRepository

CLAVE_ONBOARDING_PRECIO_COP = "onboarding_precio_cop"


class OnboardingService:
    def __init__(
        self,
        session: AsyncSession,
        auth_service: AuthService,
        parametro_comercial_service: ParametroComercialService,
        wompi_client: WompiClient,
    ):
        self.session = session
        self.cobro_repository = CobroRepository(session)
        self.fuente_repository = FuenteDePagoRepository(session)
        self.auth_service = auth_service
        self.parametro_comercial_service = parametro_comercial_service
        self.wompi_client = wompi_client

    async def esta_pagado(self, sesion: SesionUsuario) -> bool:
        tenant = await self.auth_service.obtener_tenant(sesion.tenant_id)
        if tenant is None:
            raise ValueError("Tenant no encontrado.")
        return tenant.onboarding_pagado_en is not None

    async def pagar(
        self,
        sesion: SesionUsuario,
        token: str,
        acceptance_token: str,
        accept_personal_auth: str,
    ) -> Cobro:
        if sesion.rol != RolUsuario.administrador:
            raise PermisoInsuficienteError(
                "Solo un administrador de la organización puede pagar el onboarding."
            )

        tenant = await self.auth_service.obtener_tenant(sesion.tenant_id)
        if tenant is None:
            raise ValueError("Tenant no encontrado.")
        if tenant.onboarding_pagado_en is not None:
            raise OnboardingYaPagadoError("El onboarding ya fue pagado.")

        precio = await self.parametro_comercial_service.valor_vigente(
            CLAVE_ONBOARDING_PRECIO_COP, date.today()
        )
        if precio is None:
            raise ParametroComercialFaltanteError(
                f"No hay valor vigente para el parámetro "
                f"'{CLAVE_ONBOARDING_PRECIO_COP}'."
            )

        fuente_resp = await self.wompi_client.crear_fuente_de_pago(
            tipo="CARD",
            token=token,
            customer_email=sesion.email,
            acceptance_token=acceptance_token,
            accept_personal_auth=accept_personal_auth,
        )
        id_fuente_externo = str(fuente_resp["data"]["id"])
        fuente = await self.fuente_repository.add(
            FuenteDePago(
                tenant_id=sesion.tenant_id,
                tipo=TipoFuenteDePago.tarjeta,
                pasarela=PASARELA,
                id_externo=id_fuente_externo,
                estado=EstadoFuenteDePago.disponible,
                es_recurrente=False,
                descripcion="Onboarding",
            )
        )
        await self.session.commit()

        referencia = f"onboarding-{sesion.tenant_id}-{uuid.uuid4().hex[:12]}"
        cobro = await self.cobro_repository.add(
            Cobro(
                tenant_id=sesion.tenant_id,
                concepto=ConceptoCobro.onboarding,
                fuente_de_pago_id=fuente.id,
                monto_cop=Decimal(precio),
                estado=EstadoTransaccionPago.pendiente,
                referencia=referencia,
                id_externo_transaccion=None,
            )
        )
        # Se persiste el intento ANTES de llamar a la pasarela (money-precision):
        # si el proceso muere entre la llamada y la respuesta, el registro ya
        # existe con su referencia y se puede reconciliar contra Wompi.
        await self.session.commit()

        try:
            transaccion_resp = await self.wompi_client.crear_transaccion(
                reference=referencia,
                amount_in_cents=int(precio) * 100,
                currency="COP",
                customer_email=sesion.email,
                payment_source_id=int(id_fuente_externo),
            )
        except httpx.HTTPError:
            cobro.estado = EstadoTransaccionPago.error
            await self.cobro_repository.update(cobro)
            await self.session.commit()
            raise

        cobro.id_externo_transaccion = str(transaccion_resp["data"]["id"])
        cobro = await self.cobro_repository.update(cobro)
        await self.session.commit()
        return cobro
