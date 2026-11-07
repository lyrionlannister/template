"""Punto de entrada de la API de Pulso."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.env_tools import get_or_default

app = FastAPI(title="Pulso API")

allowed_origins = [
    origin.strip()
    for origin in get_or_default("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

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
