"""Plantillas: crear, consultar, editar, eliminar, renderizar de prueba y
verificar variables faltantes sobre una audiencia."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.auth.dependencies import SesionActual
from app.templates.dependencies import TemplatesServiceDep
from app.templates.exceptions import (
    AudienciaNoEncontradaParaVerificarError,
    CategoriaRequeridaError,
    ContactoNoEncontradoParaRenderizarError,
    NombrePlantillaMetaRequeridoError,
    NombrePlantillaSentRequeridoError,
    PlantillaNoEncontradaError,
    VariableFaltanteEnRenderizadoError,
    VariableNoPermitidaError,
)
from app.templates.schemas.plantilla_schema import (
    PlantillaActualizarRequest,
    PlantillaCrearRequest,
    PlantillaRespuesta,
    PlantillasPaginadasRespuesta,
    RenderizarRequest,
    RenderizarRespuesta,
    VerificarAudienciaRequest,
    VerificarAudienciaRespuesta,
)

router = APIRouter(prefix="/templates", tags=["templates"])


def _a_respuesta(plantilla) -> PlantillaRespuesta:
    return PlantillaRespuesta.model_validate(plantilla)


@router.get("", response_model=PlantillasPaginadasRespuesta)
async def listar(
    sesion: SesionActual,
    service: TemplatesServiceDep,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
) -> PlantillasPaginadasRespuesta:
    plantillas, total = await service.listar(pagina, por_pagina)
    return PlantillasPaginadasRespuesta(
        plantillas=[_a_respuesta(p) for p in plantillas],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.post("", response_model=PlantillaRespuesta, status_code=status.HTTP_201_CREATED)
async def crear(
    body: PlantillaCrearRequest, sesion: SesionActual, service: TemplatesServiceDep
) -> PlantillaRespuesta:
    try:
        plantilla = await service.crear(
            sesion.tenant_id,
            body.nombre,
            body.canal,
            body.contenido,
            body.categoria,
            body.nombre_plantilla_meta,
            body.nombre_plantilla_sent,
        )
    except VariableNoPermitidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except (
        CategoriaRequeridaError,
        NombrePlantillaMetaRequeridoError,
        NombrePlantillaSentRequeridoError,
    ) as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    return _a_respuesta(plantilla)


@router.get("/{public_id}", response_model=PlantillaRespuesta)
async def obtener(
    public_id: UUID, sesion: SesionActual, service: TemplatesServiceDep
) -> PlantillaRespuesta:
    try:
        plantilla = await service.obtener(public_id)
    except PlantillaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return _a_respuesta(plantilla)


@router.patch("/{public_id}", response_model=PlantillaRespuesta)
async def actualizar(
    public_id: UUID,
    body: PlantillaActualizarRequest,
    sesion: SesionActual,
    service: TemplatesServiceDep,
) -> PlantillaRespuesta:
    try:
        plantilla = await service.actualizar(
            public_id,
            body.nombre,
            body.contenido,
            body.categoria,
            body.nombre_plantilla_meta,
            body.nombre_plantilla_sent,
        )
    except PlantillaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except VariableNoPermitidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except (
        CategoriaRequeridaError,
        NombrePlantillaMetaRequeridoError,
        NombrePlantillaSentRequeridoError,
    ) as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    return _a_respuesta(plantilla)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    public_id: UUID, sesion: SesionActual, service: TemplatesServiceDep
) -> None:
    try:
        await service.eliminar(public_id)
    except PlantillaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@router.post("/{public_id}/renderizar", response_model=RenderizarRespuesta)
async def renderizar(
    public_id: UUID,
    body: RenderizarRequest,
    sesion: SesionActual,
    service: TemplatesServiceDep,
) -> RenderizarRespuesta:
    try:
        texto = await service.renderizar(public_id, body.contacto_public_id)
    except PlantillaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except ContactoNoEncontradoParaRenderizarError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except VariableFaltanteEnRenderizadoError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    return RenderizarRespuesta(texto=texto)


@router.post(
    "/{public_id}/verificar-audiencia", response_model=VerificarAudienciaRespuesta
)
async def verificar_audiencia(
    public_id: UUID,
    body: VerificarAudienciaRequest,
    sesion: SesionActual,
    service: TemplatesServiceDep,
) -> VerificarAudienciaRespuesta:
    try:
        total, con_faltante = await service.verificar_audiencia(
            public_id, body.audiencia_public_id
        )
    except PlantillaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except AudienciaNoEncontradaParaVerificarError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return VerificarAudienciaRespuesta(
        total_contactos=total, contactos_con_variable_faltante=con_faltante
    )
