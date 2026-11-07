"""Panel mínimo del administrador del sistema para los planes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.app_platform.dependencies import PlanServiceDep, require_system_scope
from app.app_platform.exceptions import (
    ParametroComercialFaltanteError,
    ReglaDeIncluidosVioladaError,
)
from app.app_platform.schemas.plan_schema import (
    PlanActualizarRequest,
    PlanRequest,
    PlanRespuesta,
)

router = APIRouter(
    prefix="/app-platform/planes",
    tags=["app_platform"],
    dependencies=[Depends(require_system_scope)],
)


@router.post("", response_model=PlanRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_plan(body: PlanRequest, service: PlanServiceDep) -> PlanRespuesta:
    try:
        plan = await service.crear(body.model_dump())
    except (ReglaDeIncluidosVioladaError, ParametroComercialFaltanteError) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return PlanRespuesta.model_validate(plan)


@router.get("", response_model=list[PlanRespuesta])
async def listar_planes(service: PlanServiceDep) -> list[PlanRespuesta]:
    planes = await service.listar()
    return [PlanRespuesta.model_validate(plan) for plan in planes]


@router.patch("/{public_id}", response_model=PlanRespuesta)
async def actualizar_plan(
    public_id: UUID, body: PlanActualizarRequest, service: PlanServiceDep
) -> PlanRespuesta:
    datos = {
        campo: valor for campo, valor in body.model_dump().items() if valor is not None
    }
    try:
        plan = await service.actualizar(public_id, datos)
    except (ReglaDeIncluidosVioladaError, ParametroComercialFaltanteError) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return PlanRespuesta.model_validate(plan)
