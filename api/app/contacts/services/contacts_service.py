"""Lógica de negocio de contactos: previsualización e importación de
archivos CSV/XLSX/Parquet (ver `resources/specs/SPEC-contactos.md`)."""

import json
import uuid
from dataclasses import dataclass
from datetime import date

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
)
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.auth.services.auth_service import AuthService
from app.contacts.enums.contacts_enums import (
    EstadoImportacion,
    FormatoArchivoImportacion,
)
from app.contacts.exceptions import (
    ColumnaTelefonoInvalidaError,
    FormatoArchivoNoSoportadoError,
    LimiteDeFilasExcedidoError,
    PrevisualizacionNoEncontradaError,
    TipoDeArchivoNoCoincideError,
)
from app.contacts.models.importacion_contacto_model import ImportacionContacto
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.repositories.importacion_contacto_repository import (
    ImportacionContactoRepository,
)
from app.core.tools.file_tools import (
    read_tabular,
    read_within_limit,
    tipo_real_coincide,
)
from app.core.valkey.client import valkey_client

_CLAVE_IMPORTACION_TAMANO_MAXIMO_MB = "importacion_tamano_maximo_mb"
_PREVIEW_TTL_SEGUNDOS = 30 * 60
_MUESTRA_FILAS = 20
_EXTENSIONES_SOPORTADAS = {"csv": "csv", "xlsx": "xlsx", "parquet": "parquet"}


@dataclass
class ResultadoPrevisualizacion:
    preview_id: str
    columnas: list[str]
    muestra: list[dict[str, str]]
    total_filas: int


class ContactsService:
    def __init__(
        self,
        session: AsyncSession,
        auth_service: AuthService,
        plan_service: PlanService,
        parametro_comercial_service: ParametroComercialService,
        contacto_repository: ContactoRepository,
        importacion_repository: ImportacionContactoRepository,
    ):
        self.session = session
        self.auth_service = auth_service
        self.plan_service = plan_service
        self.parametro_comercial_service = parametro_comercial_service
        self.contacto_repository = contacto_repository
        self.importacion_repository = importacion_repository

    async def previsualizar(
        self, tenant_id: int, archivo: UploadFile
    ) -> ResultadoPrevisualizacion:
        formato = self._formato_desde_nombre(archivo.filename)
        max_bytes = await self._tamano_maximo_bytes()

        content = await read_within_limit(archivo, max_bytes)
        if not tipo_real_coincide(content, formato):
            raise TipoDeArchivoNoCoincideError(
                "El contenido del archivo no corresponde a su extensión."
            )

        filas = read_tabular(content, formato)
        total_filas = len(filas)

        limite_filas = await self._limite_filas_del_tenant(tenant_id)
        if total_filas > limite_filas:
            raise LimiteDeFilasExcedidoError(
                f"El archivo tiene {total_filas} filas; el plan vigente de "
                f"esta organización permite hasta {limite_filas}."
            )

        columnas = list(filas[0].keys()) if filas else []
        preview_id = uuid.uuid4().hex
        await valkey_client.set(
            self._clave_preview(tenant_id, preview_id),
            json.dumps(
                {
                    "nombre_archivo": archivo.filename,
                    "formato": formato,
                    "columnas": columnas,
                    "filas": filas,
                }
            ),
            ex=_PREVIEW_TTL_SEGUNDOS,
        )

        return ResultadoPrevisualizacion(
            preview_id=preview_id,
            columnas=columnas,
            muestra=filas[:_MUESTRA_FILAS],
            total_filas=total_filas,
        )

    async def confirmar_importacion(
        self,
        tenant_id: int,
        preview_id: str,
        columna_telefono: str,
        mapeo_variables: dict[str, str],
        background_tasks: BackgroundTasks,
    ) -> ImportacionContacto:
        """Lee la previsualización cacheada, crea la `ImportacionContacto`
        y borra la clave de Valkey antes de programar el procesamiento --
        así una confirmación repetida con el mismo `preview_id` siempre
        falla en la segunda llamada, nunca dispara dos importaciones."""

        clave = self._clave_preview(tenant_id, preview_id)
        crudo = await valkey_client.get(clave)
        if crudo is None:
            raise PrevisualizacionNoEncontradaError(
                "La previsualización no existe, ya expiró o ya fue confirmada."
            )

        datos = json.loads(crudo)
        filas: list[dict[str, str]] = datos["filas"]
        columnas: list[str] = datos["columnas"]

        if columna_telefono not in columnas:
            raise ColumnaTelefonoInvalidaError(
                f"'{columna_telefono}' no es una columna de este archivo."
            )

        limite_filas = await self._limite_filas_del_tenant(tenant_id)
        if len(filas) > limite_filas:
            raise LimiteDeFilasExcedidoError(
                f"El archivo tiene {len(filas)} filas; el plan vigente de "
                f"esta organización permite hasta {limite_filas}."
            )

        importacion = await self.importacion_repository.add(
            ImportacionContacto(
                tenant_id=tenant_id,
                nombre_archivo=datos["nombre_archivo"],
                formato=FormatoArchivoImportacion(datos["formato"]),
                estado=EstadoImportacion.pendiente,
                columna_telefono=columna_telefono,
                mapeo_variables=mapeo_variables,
                total_filas=len(filas),
            )
        )
        await self.session.commit()

        await valkey_client.delete(clave)

        background_tasks.add_task(
            procesar_importacion_en_segundo_plano,
            tenant_id,
            importacion.id,
            filas,
            columna_telefono,
            mapeo_variables,
        )

        return importacion

    async def _tamano_maximo_bytes(self) -> int:
        valor_mb = await self.parametro_comercial_service.valor_vigente(
            _CLAVE_IMPORTACION_TAMANO_MAXIMO_MB, date.today()
        )
        if valor_mb is None:
            raise ParametroComercialFaltanteError(
                f"Falta el parámetro comercial "
                f"'{_CLAVE_IMPORTACION_TAMANO_MAXIMO_MB}'."
            )
        return int(valor_mb * 1024 * 1024)

    async def _limite_filas_del_tenant(self, tenant_id: int) -> int:
        tenant = await self.auth_service.obtener_tenant(tenant_id)
        if tenant is None or tenant.plan_id is None:
            raise LimiteDePlanError(
                "Esta organización no tiene un plan asignado todavía."
            )
        plan = await self.plan_service.obtener(tenant.plan_id)
        if plan is None:
            raise LimiteDePlanError(
                "El plan asignado a esta organización ya no existe."
            )
        return plan.limite_filas_importacion

    @staticmethod
    def _formato_desde_nombre(nombre_archivo: str | None) -> str:
        if not nombre_archivo or "." not in nombre_archivo:
            raise FormatoArchivoNoSoportadoError(
                "El archivo no tiene una extensión reconocible."
            )
        extension = nombre_archivo.rsplit(".", 1)[-1].lower()
        formato = _EXTENSIONES_SOPORTADAS.get(extension)
        if formato is None:
            raise FormatoArchivoNoSoportadoError(
                f"Formato no soportado: .{extension}. Solo CSV, XLSX y Parquet."
            )
        return formato

    @staticmethod
    def _clave_preview(tenant_id: int, preview_id: str) -> str:
        return f"importacion:preview:{tenant_id}:{preview_id}"


async def procesar_importacion_en_segundo_plano(
    tenant_id: int,
    importacion_id: int,
    filas: list[dict[str, str]],
    columna_telefono: str,
    mapeo_variables: dict[str, str],
) -> None:
    """Corre en el `BackgroundTask`, fuera de la petición HTTP: la sesión
    del request ya cerró para cuando esto se ejecuta, así que abre la suya
    propia (ver Architecture decisions de `plan-contactos.md`). Implementación
    completa en la Tarea 5."""

    raise NotImplementedError
