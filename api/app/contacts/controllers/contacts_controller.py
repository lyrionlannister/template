"""Importación de contactos: previsualización, configuración de la
política de conflicto de variables y sus conflictos registrados."""

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
)
from app.auth.dependencies import SesionActual
from app.auth.exceptions import PermisoInsuficienteError
from app.contacts.dependencies import ContactsServiceDep
from app.contacts.exceptions import (
    ColumnaTelefonoInvalidaError,
    ConflictoNoEncontradoError,
    ConflictoYaRevertidoError,
    ContactoNoEncontradoError,
    FormatoArchivoNoSoportadoError,
    ImportacionNoEncontradaError,
    LimiteDeFilasExcedidoError,
    PrevisualizacionNoEncontradaError,
    TipoDeArchivoNoCoincideError,
)
from app.contacts.schemas.configuracion_contactos_schema import (
    ActualizarConfiguracionContactosRequest,
    ConfiguracionContactosRespuesta,
    ConflictoVariableRespuesta,
    RevertirConflictoRespuesta,
)
from app.contacts.schemas.contacto_schema import (
    ContactoRespuesta,
    ContactosPaginadosRespuesta,
)
from app.contacts.schemas.importacion_contacto_schema import (
    ConfirmarImportacionRequest,
    ContactoRechazadoRespuesta,
    EstadoImportacionRespuesta,
    ImportacionContactoRespuesta,
    PrevisualizacionImportacionRespuesta,
    RechazosPaginadosRespuesta,
)
from app.core.tools.file_tools import ArchivoDemasiadoGrandeError

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post(
    "/importaciones/previsualizar",
    response_model=PrevisualizacionImportacionRespuesta,
)
async def previsualizar_importacion(
    sesion: SesionActual,
    service: ContactsServiceDep,
    archivo: UploadFile,
) -> PrevisualizacionImportacionRespuesta:
    try:
        resultado = await service.previsualizar(sesion.tenant_id, archivo)
    except (FormatoArchivoNoSoportadoError, TipoDeArchivoNoCoincideError) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except ArchivoDemasiadoGrandeError as error:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(error)
        ) from error
    except LimiteDeFilasExcedidoError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except LimiteDePlanError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except ParametroComercialFaltanteError as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, str(error)
        ) from error

    return PrevisualizacionImportacionRespuesta(
        preview_id=resultado.preview_id,
        columnas=resultado.columnas,
        muestra=resultado.muestra,
        total_filas=resultado.total_filas,
    )


@router.post(
    "/importaciones",
    response_model=ImportacionContactoRespuesta,
)
async def confirmar_importacion(
    body: ConfirmarImportacionRequest,
    sesion: SesionActual,
    service: ContactsServiceDep,
    background_tasks: BackgroundTasks,
) -> ImportacionContactoRespuesta:
    try:
        importacion = await service.confirmar_importacion(
            sesion.tenant_id,
            body.preview_id,
            body.columna_telefono,
            body.mapeo_variables,
            background_tasks,
        )
    except PrevisualizacionNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except ColumnaTelefonoInvalidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except LimiteDeFilasExcedidoError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error

    return ImportacionContactoRespuesta(
        public_id=importacion.public_id,
        estado=importacion.estado,
        total_filas=importacion.total_filas,
    )


@router.get(
    "/importaciones/{importacion_public_id}",
    response_model=EstadoImportacionRespuesta,
)
async def obtener_estado_importacion(
    importacion_public_id: UUID,
    sesion: SesionActual,
    service: ContactsServiceDep,
) -> EstadoImportacionRespuesta:
    try:
        importacion = await service.obtener_estado_importacion(importacion_public_id)
    except ImportacionNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error

    return EstadoImportacionRespuesta(
        public_id=importacion.public_id,
        estado=importacion.estado,
        total_filas=importacion.total_filas,
        filas_aceptadas=importacion.filas_aceptadas,
        filas_rechazadas=importacion.filas_rechazadas,
        filas_con_advertencia=importacion.filas_con_advertencia,
        motivo_fallo=importacion.motivo_fallo,
    )


@router.get(
    "/importaciones/{importacion_public_id}/rechazos",
    response_model=RechazosPaginadosRespuesta,
)
async def listar_rechazos_de_importacion(
    importacion_public_id: UUID,
    sesion: SesionActual,
    service: ContactsServiceDep,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=200),
) -> RechazosPaginadosRespuesta:
    try:
        rechazos, total = await service.listar_rechazos(
            importacion_public_id, pagina, por_pagina
        )
    except ImportacionNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error

    return RechazosPaginadosRespuesta(
        rechazos=[
            ContactoRechazadoRespuesta(
                fila_cruda=rechazo.fila_cruda, motivo=rechazo.motivo
            )
            for rechazo in rechazos
        ],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.get(
    "/contactos",
    response_model=ContactosPaginadosRespuesta,
)
async def listar_contactos(
    sesion: SesionActual,
    service: ContactsServiceDep,
    telefono: str | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=200),
) -> ContactosPaginadosRespuesta:
    contactos, total = await service.listar_contactos(pagina, por_pagina, telefono)
    return ContactosPaginadosRespuesta(
        contactos=[
            ContactoRespuesta(
                public_id=contacto.public_id,
                telefono=contacto.telefono,
                variables=contacto.variables,
                creado_en=contacto.creado_en,
            )
            for contacto in contactos
        ],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.get(
    "/contactos/{contacto_public_id}",
    response_model=ContactoRespuesta,
)
async def obtener_contacto(
    contacto_public_id: UUID,
    sesion: SesionActual,
    service: ContactsServiceDep,
) -> ContactoRespuesta:
    try:
        contacto = await service.obtener_contacto(contacto_public_id)
    except ContactoNoEncontradoError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return ContactoRespuesta(
        public_id=contacto.public_id,
        telefono=contacto.telefono,
        variables=contacto.variables,
        creado_en=contacto.creado_en,
    )


@router.get(
    "/configuracion",
    response_model=ConfiguracionContactosRespuesta,
)
async def obtener_configuracion(
    sesion: SesionActual, service: ContactsServiceDep
) -> ConfiguracionContactosRespuesta:
    politica = await service.obtener_politica_conflicto()
    return ConfiguracionContactosRespuesta(politica_conflicto_variables=politica)


@router.put(
    "/configuracion",
    response_model=ConfiguracionContactosRespuesta,
)
async def actualizar_configuracion(
    body: ActualizarConfiguracionContactosRequest,
    sesion: SesionActual,
    service: ContactsServiceDep,
) -> ConfiguracionContactosRespuesta:
    try:
        configuracion = await service.actualizar_politica_conflicto(
            sesion, body.politica_conflicto_variables
        )
    except PermisoInsuficienteError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    return ConfiguracionContactosRespuesta(
        politica_conflicto_variables=configuracion.politica_conflicto_variables
    )


@router.get(
    "/contactos/{contacto_public_id}/conflictos",
    response_model=list[ConflictoVariableRespuesta],
)
async def listar_conflictos(
    contacto_public_id: UUID,
    sesion: SesionActual,
    service: ContactsServiceDep,
) -> list[ConflictoVariableRespuesta]:
    try:
        conflictos = await service.listar_conflictos_de_contacto(contacto_public_id)
    except ContactoNoEncontradoError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return [
        ConflictoVariableRespuesta(
            public_id=conflicto.public_id,
            clave=conflicto.clave,
            valor_anterior=conflicto.valor_anterior,
            valor_nuevo=conflicto.valor_nuevo,
            revertido_en=conflicto.revertido_en,
            creado_en=conflicto.creado_en,
        )
        for conflicto in conflictos
    ]


@router.post(
    "/conflictos/{conflicto_public_id}/revertir",
    response_model=RevertirConflictoRespuesta,
)
async def revertir_conflicto(
    conflicto_public_id: UUID,
    sesion: SesionActual,
    service: ContactsServiceDep,
) -> RevertirConflictoRespuesta:
    try:
        await service.revertir_conflicto(conflicto_public_id)
    except ConflictoNoEncontradoError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except ConflictoYaRevertidoError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return RevertirConflictoRespuesta(estado="revertido")
