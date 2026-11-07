"""Importación de contactos: previsualización (confirmación llega en la
Tarea 4/6)."""

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
)
from app.auth.dependencies import SesionActual
from app.contacts.dependencies import ContactsServiceDep
from app.contacts.exceptions import (
    FormatoArchivoNoSoportadoError,
    LimiteDeFilasExcedidoError,
    TipoDeArchivoNoCoincideError,
)
from app.contacts.schemas.importacion_contacto_schema import (
    PrevisualizacionImportacionRespuesta,
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
