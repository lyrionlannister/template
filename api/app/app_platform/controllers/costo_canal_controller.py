"""Panel mínimo del administrador del sistema para el histórico de costos
por canal. Toda ruta exige alcance de administrador del sistema."""

from datetime import date

from fastapi import APIRouter, Depends

from app.app_platform.dependencies import CostoCanalServiceDep, require_system_scope
from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.schemas.costo_canal_schema import (
    CostoCanalRespuesta,
    RegistrarCostoCanalRequest,
)

router = APIRouter(
    prefix="/app-platform/costos",
    tags=["app_platform"],
    dependencies=[Depends(require_system_scope)],
)


@router.post("", response_model=CostoCanalRespuesta)
async def registrar_costo(
    datos: RegistrarCostoCanalRequest, service: CostoCanalServiceDep
) -> CostoCanalRespuesta:
    costo = await service.registrar_costo(**datos.model_dump())
    return CostoCanalRespuesta.model_validate(costo)


@router.get("/historico", response_model=list[CostoCanalRespuesta])
async def historico(
    canal: CanalMensajeria,
    service: CostoCanalServiceDep,
    categoria: CategoriaMensaje | None = None,
) -> list[CostoCanalRespuesta]:
    costos = await service.historico(canal, categoria)
    return [CostoCanalRespuesta.model_validate(costo) for costo in costos]


@router.get("/vigente", response_model=CostoCanalRespuesta | None)
async def vigente(
    canal: CanalMensajeria,
    service: CostoCanalServiceDep,
    categoria: CategoriaMensaje | None = None,
    fecha: date | None = None,
) -> CostoCanalRespuesta | None:
    costo = await service.costo_vigente(canal, categoria, fecha or date.today())
    return CostoCanalRespuesta.model_validate(costo) if costo else None
