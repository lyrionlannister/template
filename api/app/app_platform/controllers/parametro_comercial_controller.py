"""Panel mínimo del administrador del sistema para parámetros comerciales
de valor único (trial, onboarding, comisión de Wompi, etc.)."""

from datetime import date

from fastapi import APIRouter, Depends

from app.app_platform.dependencies import ParametroComercialServiceDep
from app.app_platform.schemas.parametro_comercial_schema import (
    ParametroComercialRegistrarRequest,
    ParametroComercialRespuesta,
)
from app.auth.dependencies import require_system_scope

router = APIRouter(
    prefix="/app-platform/parametros-comerciales",
    tags=["app_platform"],
    dependencies=[Depends(require_system_scope)],
)


@router.post("", response_model=ParametroComercialRespuesta)
async def registrar(
    body: ParametroComercialRegistrarRequest, service: ParametroComercialServiceDep
) -> ParametroComercialRespuesta:
    registro = await service.registrar(
        body.clave, body.valor, body.fuente, body.vigente_desde
    )
    return ParametroComercialRespuesta.model_validate(registro)


@router.get("/historico", response_model=list[ParametroComercialRespuesta])
async def historico(
    clave: str, service: ParametroComercialServiceDep
) -> list[ParametroComercialRespuesta]:
    registros = await service.historico(clave)
    return [ParametroComercialRespuesta.model_validate(r) for r in registros]


@router.get("/vigente", response_model=ParametroComercialRespuesta | None)
async def vigente(
    clave: str, service: ParametroComercialServiceDep, fecha: date | None = None
) -> ParametroComercialRespuesta | None:
    registro = await service.registro_vigente(clave, fecha or date.today())
    return ParametroComercialRespuesta.model_validate(registro) if registro else None
