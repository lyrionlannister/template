"""Tarea programada de cobro recurrente de suscripciones. Corre dentro del
mismo proceso de la API con APScheduler -- decisión confirmada por Luis el
2026-11-07: sin infraestructura nueva (ni cron del SO, ni servicio aparte),
razonable para el volumen de tenants de esta fase."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.dependencies import get_auth_service
from app.billing.clients.wompi_client import WompiClient
from app.billing.services.suscripcion_service import SuscripcionService
from app.core.database.session import async_session_factory

logger = logging.getLogger("pulso.billing.scheduler")

_scheduler = AsyncIOScheduler()
_JOB_ID = "cobro_recurrente_diario"


async def _ejecutar_cobro_diario() -> None:
    async with async_session_factory() as session:
        wompi_client = WompiClient()
        try:
            parametro_comercial_service = ParametroComercialService(session)
            plan_service = PlanService(
                session,
                CostoCanalService(session),
                TipoCambioService(session),
                parametro_comercial_service,
            )
            # `get_auth_service` es la dependencia de FastAPI de auth, pero es
            # una función común: se llama directo aquí para no importar
            # `auth.repositories` desde billing (prohibido por
            # `.importlinter`, igual que cualquier otro dominio).
            auth_service = get_auth_service(
                session, plan_service, parametro_comercial_service
            )
            suscripcion_service = SuscripcionService(
                session, wompi_client, auth_service, plan_service
            )
            procesadas = await suscripcion_service.cobrar_ciclo()
            logger.info("cobro recurrente: %s suscripciones procesadas", procesadas)
        except Exception:
            logger.exception("cobro recurrente: fallo ejecutando el ciclo diario")
        finally:
            await wompi_client.cerrar()


def iniciar_scheduler() -> None:
    if _scheduler.get_job(_JOB_ID) is None:
        _scheduler.add_job(
            _ejecutar_cobro_diario,
            CronTrigger(hour=3, minute=0),
            id=_JOB_ID,
            replace_existing=True,
        )
    if not _scheduler.running:
        _scheduler.start()


def detener_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
