"""Reglas de negocio de los planes.

`crear`/`actualizar` exigen alcance de sistema y validan la regla de
rentabilidad del 30 % contra el costo e histórico vigentes: el costo de
los incluidos no puede superar el 30 % del neto de la suscripción tras la
comisión de Wompi. `verificar_limite_usuarios`/`verificar_limite_numeros_whatsapp` los
usa cualquier dominio que dé de alta un usuario o un número de WhatsApp
(auth, messaging) — no exigen alcance de sistema: son un chequeo de
negocio normal dentro del tenant.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
    ReglaDeIncluidosVioladaError,
)
from app.app_platform.models.plan_model import Plan
from app.app_platform.repositories.plan_repository import PlanRepository
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.core.database.tenant_context import is_system_scope

PAR_USD_COP = "USD/COP"
CLAVE_COMISION_WOMPI_PORCENTAJE = "comision_wompi_porcentaje"
CLAVE_COMISION_WOMPI_FIJO = "comision_wompi_fijo_cop"
CLAVE_COMISION_WOMPI_IVA_PORCENTAJE = "comision_wompi_iva_porcentaje"


class AccesoDeAdministradorRequeridoError(PermissionError):
    pass


def _exigir_alcance_de_sistema() -> None:
    if not is_system_scope():
        raise AccesoDeAdministradorRequeridoError(
            "Esta operación requiere alcance de administrador del sistema."
        )


class PlanService:
    def __init__(
        self,
        session: AsyncSession,
        costo_canal_service: CostoCanalService,
        tipo_cambio_service: TipoCambioService,
        parametro_comercial_service: ParametroComercialService,
    ):
        self.session = session
        self.repository = PlanRepository(session)
        self.costo_canal_service = costo_canal_service
        self.tipo_cambio_service = tipo_cambio_service
        self.parametro_comercial_service = parametro_comercial_service

    async def listar(self) -> list[Plan]:
        return await self.repository.listar()

    async def obtener(self, plan_id: int) -> Plan | None:
        return await self.repository.get_by_id(plan_id)

    async def obtener_por_nombre(self, nombre: str) -> Plan | None:
        return await self.repository.obtener_por_nombre(nombre)

    async def crear(self, datos: dict) -> Plan:
        _exigir_alcance_de_sistema()
        await self._validar_regla_30_porciento(
            mensajes_incluidos=datos["mensajes_marketing_incluidos"],
            precio_mensual=datos["precio_mensual_cop"],
        )
        creado = await self.repository.add(Plan(**datos))
        await self.session.commit()
        return creado

    async def actualizar(self, public_id: UUID, datos: dict) -> Plan:
        _exigir_alcance_de_sistema()
        plan = await self.repository.obtener_por_public_id(public_id)
        if plan is None:
            raise ValueError("Plan no encontrado.")

        mensajes_incluidos = datos.get(
            "mensajes_marketing_incluidos", plan.mensajes_marketing_incluidos
        )
        precio_mensual = datos.get("precio_mensual_cop", plan.precio_mensual_cop)
        await self._validar_regla_30_porciento(mensajes_incluidos, precio_mensual)

        for campo, valor in datos.items():
            setattr(plan, campo, valor)
        actualizado = await self.repository.update(plan)
        await self.session.commit()
        return actualizado

    async def verificar_limite_usuarios(self, plan: Plan, conteo_actual: int) -> None:
        if conteo_actual >= plan.max_usuarios:
            raise LimiteDePlanError(
                f"El plan {plan.nombre} permite hasta {plan.max_usuarios} usuarios. "
                "Sube de plan para agregar más desde el panel de administración."
            )

    async def verificar_limite_numeros_whatsapp(
        self, plan: Plan, conteo_actual: int
    ) -> None:
        if conteo_actual >= plan.max_whatsapp_numeros:
            raise LimiteDePlanError(
                f"El plan {plan.nombre} permite hasta {plan.max_whatsapp_numeros} "
                "números de WhatsApp. Sube de plan para conectar más."
            )

    async def _validar_regla_30_porciento(
        self, mensajes_incluidos: int, precio_mensual: Decimal
    ) -> None:
        hoy = date.today()

        costo_marketing = await self.costo_canal_service.costo_vigente(
            CanalMensajeria.whatsapp, CategoriaMensaje.marketing, hoy
        )
        if costo_marketing is None:
            raise ParametroComercialFaltanteError(
                "No hay costo vigente de WhatsApp marketing: registra uno antes de "
                "crear o editar un plan."
            )
        trm = await self.tipo_cambio_service.valor_vigente(PAR_USD_COP, hoy)
        if trm is None:
            raise ParametroComercialFaltanteError(
                f"No hay TRM vigente para {PAR_USD_COP}."
            )
        comision_porcentaje = await self.parametro_comercial_service.valor_vigente(
            CLAVE_COMISION_WOMPI_PORCENTAJE, hoy
        )
        comision_fijo = await self.parametro_comercial_service.valor_vigente(
            CLAVE_COMISION_WOMPI_FIJO, hoy
        )
        comision_iva_porcentaje = await self.parametro_comercial_service.valor_vigente(
            CLAVE_COMISION_WOMPI_IVA_PORCENTAJE, hoy
        )
        if comision_porcentaje is None or comision_fijo is None:
            raise ParametroComercialFaltanteError(
                "Faltan los parámetros de comisión de Wompi."
            )
        if comision_iva_porcentaje is None:
            raise ParametroComercialFaltanteError(
                "Falta el parámetro de IVA sobre la comisión de Wompi."
            )

        costo_marketing_cop = (costo_marketing.costo_unitario * trm.valor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        costo_incluidos = (costo_marketing_cop * mensajes_incluidos).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )

        comision = (
            (precio_mensual * comision_porcentaje + comision_fijo)
            * (1 + comision_iva_porcentaje)
        ).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        neto = precio_mensual - comision
        limite_30_porciento = (neto * Decimal("0.30")).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )

        if costo_incluidos > limite_30_porciento:
            raise ReglaDeIncluidosVioladaError(
                f"Los {mensajes_incluidos} mensajes de marketing incluidos cuestan "
                f"${costo_incluidos} COP al costo vigente de Meta (${costo_marketing_cop} "
                f"COP/mensaje, TRM {trm.valor}). Eso supera el 30 % del neto tras "
                f"Wompi (${limite_30_porciento} COP, neto ${neto} COP sobre "
                f"${precio_mensual} COP de suscripción). Baja los incluidos o sube "
                "el precio."
            )
