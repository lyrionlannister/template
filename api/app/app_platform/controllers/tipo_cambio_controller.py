"""Panel mínimo del administrador del sistema para la TRM."""

from datetime import date

from fastapi import APIRouter, Depends

from app.app_platform.dependencies import TipoCambioServiceDep
from app.auth.dependencies import require_system_scope
from app.app_platform.schemas.tipo_cambio_schema import (
    TipoCambioRegistrarRequest,
    TipoCambioRespuesta,
)

router = APIRouter(
    prefix="/app-platform/tipo-cambio",
    tags=["app_platform"],
    dependencies=[Depends(require_system_scope)],
)


@router.post("", response_model=TipoCambioRespuesta)
async def registrar(
    body: TipoCambioRegistrarRequest, service: TipoCambioServiceDep
) -> TipoCambioRespuesta:
    registro = await service.registrar(
        body.par, body.valor, body.fuente, body.vigente_desde
    )
    return TipoCambioRespuesta.model_validate(registro)


@router.get("/historico", response_model=list[TipoCambioRespuesta])
async def historico(
    par: str, service: TipoCambioServiceDep
) -> list[TipoCambioRespuesta]:
    registros = await service.historico(par)
    return [TipoCambioRespuesta.model_validate(registro) for registro in registros]


@router.get("/vigente", response_model=TipoCambioRespuesta | None)
async def vigente(
    par: str, service: TipoCambioServiceDep, fecha: date | None = None
) -> TipoCambioRespuesta | None:
    registro = await service.valor_vigente(par, fecha or date.today())
    return TipoCambioRespuesta.model_validate(registro) if registro else None
