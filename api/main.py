"""Punto de entrada de la API de Pulso."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.app_platform.controllers.costo_canal_controller import (
    router as costo_canal_router,
)
from app.auth.controllers.auth_controller import router as auth_router
from app.core.config.env_tools import get_or_default
from app.core.security.origin_check_middleware import OriginCheckMiddleware
from app.core.security.security_headers_middleware import SecurityHeadersMiddleware

app = FastAPI(title="Pulso API")
app.include_router(costo_canal_router)
app.include_router(auth_router)

allowed_origins = [
    origin.strip()
    for origin in get_or_default("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

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
