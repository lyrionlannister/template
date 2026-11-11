"""Punto de entrada de la API de Pulso."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.app_platform.controllers.costo_canal_controller import (
    router as costo_canal_router,
)
from app.app_platform.controllers.parametro_comercial_controller import (
    router as parametro_comercial_router,
)
from app.app_platform.controllers.plan_controller import router as plan_router
from app.app_platform.controllers.tipo_cambio_controller import (
    router as tipo_cambio_router,
)
from app.audiences.controllers.audiencias_controller import (
    router as audiences_router,
)
from app.auth.controllers.auth_controller import router as auth_router
from app.billing.controllers.fuente_de_pago_controller import (
    router as fuente_de_pago_router,
)
from app.billing.controllers.onboarding_controller import (
    router as onboarding_router,
)
from app.billing.controllers.saldo_controller import router as saldo_router
from app.billing.controllers.suscripcion_controller import (
    router as suscripcion_router,
)
from app.billing.controllers.webhook_controller import router as webhook_router
from app.billing.scheduler import detener_scheduler, iniciar_scheduler
from app.contacts.controllers.contacts_controller import (
    router as contacts_router,
)
from app.core.config.settings import get_settings
from app.core.security.origin_check_middleware import OriginCheckMiddleware
from app.core.security.security_headers_middleware import SecurityHeadersMiddleware
from app.messaging.controllers.messaging_controller import (
    router as messaging_router,
)
from app.messaging.controllers.plantilla_otp_plataforma_controller import (
    router as plantilla_otp_plataforma_router,
)
from app.templates.controllers.templates_controller import (
    router as templates_router,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    iniciar_scheduler()
    yield
    detener_scheduler()


app = FastAPI(title="Pulso API", lifespan=lifespan)
app.include_router(costo_canal_router)
app.include_router(plan_router)
app.include_router(tipo_cambio_router)
app.include_router(parametro_comercial_router)
app.include_router(auth_router)
app.include_router(webhook_router)
app.include_router(onboarding_router)
app.include_router(fuente_de_pago_router)
app.include_router(suscripcion_router)
app.include_router(saldo_router)
app.include_router(contacts_router)
app.include_router(audiences_router)
app.include_router(templates_router)
app.include_router(messaging_router)
app.include_router(plantilla_otp_plataforma_router)

allowed_origins = get_settings().app.allowed_origins

# Orden (Starlette: lo último agregado queda más externo): OriginCheck y
# SecurityHeaders primero, CORS al final para que envuelva todo, incluidas
# las respuestas de error y el preflight.
app.add_middleware(OriginCheckMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
