"""Audiencias: crear, consultar, editar, duplicar y eliminar filtros
guardados sobre contactos."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.audiences.dependencies import AudienciasServiceDep
from app.audiences.exceptions import (
    AudienciaEstaticaInmutableError,
    AudienciaNoEncontradaError,
)
from app.audiences.schemas.audiencia_schema import (
    AudienciaActualizarRequest,
    AudienciaCrearRequest,
    AudienciaRespuesta,
    AudienciasPaginadasRespuesta,
    CamposDisponiblesRespuesta,
    DuplicarAudienciaRequest,
    VistaPreviaRequest,
    VistaPreviaRespuesta,
)
from app.auth.dependencies import SesionActual
from app.contacts.exceptions import FiltroInvalidoError

router = APIRouter(prefix="/audiences", tags=["audiences"])


async def _a_respuesta(audiencia, service: AudienciasServiceDep) -> AudienciaRespuesta:
    conteo = await service.contar(audiencia)
    return AudienciaRespuesta(
        public_id=audiencia.public_id,
        nombre=audiencia.nombre,
        tipo=audiencia.tipo,
        filtro=audiencia.filtro,
        conteo=conteo,
        congelada_en=audiencia.congelada_en,
        creado_en=audiencia.creado_en,
    )


@router.get("/campos", response_model=CamposDisponiblesRespuesta)
async def campos_disponibles(
    sesion: SesionActual, service: AudienciasServiceDep
) -> CamposDisponiblesRespuesta:
    campos = await service.campos_disponibles()
    return CamposDisponiblesRespuesta.model_validate({"campos": campos})


@router.post("/vista-previa", response_model=VistaPreviaRespuesta)
async def vista_previa(
    body: VistaPreviaRequest, sesion: SesionActual, service: AudienciasServiceDep
) -> VistaPreviaRespuesta:
    try:
        conteo = await service.vista_previa(body.filtro)
    except FiltroInvalidoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return VistaPreviaRespuesta(conteo=conteo)


@router.get("", response_model=AudienciasPaginadasRespuesta)
async def listar(
    sesion: SesionActual,
    service: AudienciasServiceDep,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
) -> AudienciasPaginadasRespuesta:
    audiencias, total = await service.listar(pagina, por_pagina)
    respuestas = [await _a_respuesta(audiencia, service) for audiencia in audiencias]
    return AudienciasPaginadasRespuesta(
        audiencias=respuestas, total=total, pagina=pagina, por_pagina=por_pagina
    )


@router.post("", response_model=AudienciaRespuesta, status_code=status.HTTP_201_CREATED)
async def crear(
    body: AudienciaCrearRequest, sesion: SesionActual, service: AudienciasServiceDep
) -> AudienciaRespuesta:
    try:
        audiencia = await service.crear(
            sesion.tenant_id, body.nombre, body.tipo, body.filtro
        )
    except FiltroInvalidoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return await _a_respuesta(audiencia, service)


@router.get("/{public_id}", response_model=AudienciaRespuesta)
async def obtener(
    public_id: UUID, sesion: SesionActual, service: AudienciasServiceDep
) -> AudienciaRespuesta:
    try:
        audiencia = await service.obtener(public_id)
    except AudienciaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return await _a_respuesta(audiencia, service)


@router.patch("/{public_id}", response_model=AudienciaRespuesta)
async def actualizar(
    public_id: UUID,
    body: AudienciaActualizarRequest,
    sesion: SesionActual,
    service: AudienciasServiceDep,
) -> AudienciaRespuesta:
    try:
        audiencia = await service.actualizar(public_id, body.nombre, body.filtro)
    except AudienciaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except AudienciaEstaticaInmutableError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except FiltroInvalidoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return await _a_respuesta(audiencia, service)


@router.post("/{public_id}/duplicar", response_model=AudienciaRespuesta)
async def duplicar(
    public_id: UUID,
    body: DuplicarAudienciaRequest,
    sesion: SesionActual,
    service: AudienciasServiceDep,
) -> AudienciaRespuesta:
    try:
        audiencia = await service.duplicar(public_id, body.tipo)
    except AudienciaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except FiltroInvalidoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return await _a_respuesta(audiencia, service)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    public_id: UUID, sesion: SesionActual, service: AudienciasServiceDep
) -> None:
    try:
        await service.eliminar(public_id)
    except AudienciaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
