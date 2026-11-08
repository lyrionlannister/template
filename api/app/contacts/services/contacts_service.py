"""Lógica de negocio de contactos: previsualización e importación de
archivos CSV/XLSX/Parquet."""

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

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
from app.auth.enums.auth_enums import RolUsuario
from app.auth.exceptions import PermisoInsuficienteError
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.auth_service import AuthService
from app.contacts.enums.contacts_enums import (
    EstadoImportacion,
    FormatoArchivoImportacion,
    PoliticaConflictoVariables,
)
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
from app.contacts.models.configuracion_contactos_model import ConfiguracionContactos
from app.contacts.models.conflicto_variable_model import ConflictoVariableContacto
from app.contacts.models.contacto_model import Contacto
from app.contacts.models.contacto_rechazado_model import ContactoRechazado
from app.contacts.models.importacion_contacto_model import ImportacionContacto
from app.contacts.repositories.configuracion_contactos_repository import (
    ConfiguracionContactosRepository,
)
from app.contacts.repositories.conflicto_variable_repository import (
    ConflictoVariableRepository,
)
from app.contacts.repositories.contacto_rechazado_repository import (
    ContactoRechazadoRepository,
)
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.repositories.importacion_contacto_repository import (
    ImportacionContactoRepository,
)
from app.contacts.utils.telefono_utils import normalizar_telefono_e164
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant
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
_CONTADOR_COMMIT_CADA = 50


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
        configuracion_repository: ConfiguracionContactosRepository,
        conflicto_repository: ConflictoVariableRepository,
        rechazado_repository: ContactoRechazadoRepository,
    ):
        self.session = session
        self.auth_service = auth_service
        self.plan_service = plan_service
        self.parametro_comercial_service = parametro_comercial_service
        self.contacto_repository = contacto_repository
        self.importacion_repository = importacion_repository
        self.configuracion_repository = configuracion_repository
        self.conflicto_repository = conflicto_repository
        self.rechazado_repository = rechazado_repository

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

    async def listar_contactos(
        self, pagina: int, por_pagina: int, busqueda_telefono: str | None
    ) -> tuple[list[Contacto], int]:
        total = await self.contacto_repository.contar(busqueda_telefono)
        contactos = await self.contacto_repository.listar(
            por_pagina, (pagina - 1) * por_pagina, busqueda_telefono
        )
        return contactos, total

    async def obtener_contacto(self, public_id: UUID) -> Contacto:
        contacto = await self.contacto_repository.obtener_por_public_id(public_id)
        if contacto is None:
            raise ContactoNoEncontradoError(
                "El contacto no existe o no pertenece a esta organización."
            )
        return contacto

    async def obtener_estado_importacion(self, public_id: UUID) -> ImportacionContacto:
        importacion = await self.importacion_repository.obtener_por_public_id(public_id)
        if importacion is None:
            raise ImportacionNoEncontradaError(
                "La importación no existe o no pertenece a esta organización."
            )
        return importacion

    async def listar_rechazos(
        self, public_id: UUID, pagina: int, por_pagina: int
    ) -> tuple[list[ContactoRechazado], int]:
        importacion = await self.obtener_estado_importacion(public_id)
        total = await self.rechazado_repository.contar_por_importacion(importacion.id)
        rechazos = await self.rechazado_repository.listar_por_importacion(
            importacion.id, por_pagina, (pagina - 1) * por_pagina
        )
        return rechazos, total

    async def obtener_politica_conflicto(self) -> PoliticaConflictoVariables:
        configuracion = await self.configuracion_repository.obtener()
        if configuracion is None:
            return PoliticaConflictoVariables.ultimo_gana
        return configuracion.politica_conflicto_variables

    async def actualizar_politica_conflicto(
        self, sesion: SesionUsuario, politica: PoliticaConflictoVariables
    ) -> ConfiguracionContactos:
        """Solo un administrador de la organización puede cambiar esta
        política -- mismo criterio que invitar usuarios."""

        if sesion.rol != RolUsuario.administrador:
            raise PermisoInsuficienteError(
                "Solo un administrador de la organización puede cambiar "
                "esta configuración."
            )

        configuracion = await self.configuracion_repository.obtener()
        if configuracion is None:
            configuracion = await self.configuracion_repository.add(
                ConfiguracionContactos(
                    tenant_id=sesion.tenant_id,
                    politica_conflicto_variables=politica,
                )
            )
        else:
            configuracion.politica_conflicto_variables = politica
            configuracion = await self.configuracion_repository.update(configuracion)
        await self.session.commit()
        return configuracion

    async def listar_conflictos_de_contacto(
        self, contacto_public_id: UUID
    ) -> list[ConflictoVariableContacto]:
        contacto = await self.contacto_repository.obtener_por_public_id(
            contacto_public_id
        )
        if contacto is None:
            raise ContactoNoEncontradoError(
                "El contacto no existe o no pertenece a esta organización."
            )
        resultado = await self.session.execute(
            self.conflicto_repository.scoped()
            .where(ConflictoVariableContacto.contacto_id == contacto.id)
            .order_by(ConflictoVariableContacto.creado_en.desc())
        )
        return list(resultado.scalars().all())

    async def revertir_conflicto(self, conflicto_public_id: UUID) -> Contacto:
        """Pone de vuelta `valor_anterior` en esa clave del contacto --
        reversión puntual y auditada de un conflicto ya registrado, no un
        CRUD abierto sobre `variables`."""

        conflicto = await self.conflicto_repository.obtener_por_public_id(
            conflicto_public_id
        )
        if conflicto is None:
            raise ConflictoNoEncontradoError(
                "El conflicto no existe o no pertenece a esta organización."
            )
        if conflicto.revertido_en is not None:
            raise ConflictoYaRevertidoError("Este conflicto ya fue revertido antes.")

        contacto = await self.contacto_repository.get_by_id(conflicto.contacto_id)
        if contacto is None:
            raise ConflictoNoEncontradoError(
                "El contacto de este conflicto ya no existe."
            )

        contacto.variables = {
            **contacto.variables,
            conflicto.clave: conflicto.valor_anterior,
        }
        await self.contacto_repository.update(contacto)

        conflicto.revertido_en = datetime.now(UTC)
        await self.conflicto_repository.update(conflicto)
        await self.session.commit()
        return contacto

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


def fusionar_variables_no_destructivo(
    existentes: dict[str, str], nuevas: dict[str, str]
) -> dict[str, str]:
    """La nueva fila solo sobrescribe las claves que trae con valor no
    vacío; nunca pisa un dato existente con un vacío ni borra una clave
    que la nueva fila no trae."""

    return existentes | {clave: valor for clave, valor in nuevas.items() if valor}


def detectar_conflictos(
    existentes: dict[str, str], nuevas: dict[str, str]
) -> dict[str, str]:
    """Claves donde el valor existente y el nuevo son ambos no vacíos y
    distintos -- un vacío nunca es conflicto, es simplemente "no trae
    dato". Devuelve `{clave: valor_anterior}` de cada conflicto real."""

    return {
        clave: existentes[clave]
        for clave, valor in nuevas.items()
        if valor and existentes.get(clave) and existentes[clave] != valor
    }


async def _aplicar_variables(
    tenant_id: int,
    importacion_id: int,
    contacto: Contacto,
    variables_nuevas: dict[str, str],
    politica: PoliticaConflictoVariables,
    contacto_repository: ContactoRepository,
    conflicto_repository: ConflictoVariableRepository,
) -> bool:
    """Aplica el merge no destructivo sobre un contacto ya existente,
    registrando cada conflicto real sin importar la política, y devuelve
    si la fila tuvo al menos un conflicto (para el contador de
    advertencias)."""

    conflictos = detectar_conflictos(contacto.variables, variables_nuevas)
    for clave, valor_anterior in conflictos.items():
        await conflicto_repository.add(
            ConflictoVariableContacto(
                tenant_id=tenant_id,
                contacto_id=contacto.id,
                importacion_id=importacion_id,
                clave=clave,
                valor_anterior=valor_anterior,
                valor_nuevo=variables_nuevas[clave],
            )
        )

    if politica == PoliticaConflictoVariables.no_pisar_marcar_advertencia:
        variables_a_aplicar = {
            clave: valor
            for clave, valor in variables_nuevas.items()
            if clave not in conflictos
        }
    else:
        variables_a_aplicar = variables_nuevas

    contacto.variables = fusionar_variables_no_destructivo(
        contacto.variables, variables_a_aplicar
    )
    await contacto_repository.update(contacto)
    return bool(conflictos)


async def procesar_importacion_en_segundo_plano(
    tenant_id: int,
    importacion_id: int,
    filas: list[dict[str, str]],
    columna_telefono: str,
    mapeo_variables: dict[str, str],
) -> None:
    """Corre en el `BackgroundTask`, fuera de la petición HTTP: la sesión
    del request ya cerró para cuando esto se ejecuta, así que abre la
    suya propia y recibe el `tenant_id` de forma explícita en vez de
    depender del contexto de la petición, que ya no existe."""

    async with async_session_factory() as session:
        importacion_repository = ImportacionContactoRepository(session)
        contacto_repository = ContactoRepository(session)
        rechazado_repository = ContactoRechazadoRepository(session)
        configuracion_repository = ConfiguracionContactosRepository(session)
        conflicto_repository = ConflictoVariableRepository(session)

        with set_current_tenant(tenant_id):
            importacion = await importacion_repository.get_by_id(importacion_id)
            if importacion is None:
                return

            configuracion = await configuracion_repository.obtener()
            politica = (
                configuracion.politica_conflicto_variables
                if configuracion is not None
                else PoliticaConflictoVariables.ultimo_gana
            )

            importacion.estado = EstadoImportacion.procesando
            await importacion_repository.update(importacion)
            await session.commit()

            try:
                aceptadas = 0
                rechazadas = 0
                con_advertencia = 0
                for indice, fila in enumerate(filas, start=1):
                    try:
                        telefono = normalizar_telefono_e164(
                            fila.get(columna_telefono, "")
                        )
                    except ValueError as error:
                        await rechazado_repository.add(
                            ContactoRechazado(
                                tenant_id=tenant_id,
                                importacion_id=importacion_id,
                                fila_cruda=fila,
                                motivo=str(error),
                            )
                        )
                        rechazadas += 1
                    else:
                        variables_nuevas = {
                            nombre_variable: fila.get(columna_origen, "")
                            for columna_origen, nombre_variable in (
                                mapeo_variables.items()
                            )
                        }
                        contacto = await contacto_repository.obtener_por_telefono(
                            telefono
                        )
                        if contacto is None:
                            await contacto_repository.add(
                                Contacto(
                                    tenant_id=tenant_id,
                                    telefono=telefono,
                                    variables=variables_nuevas,
                                )
                            )
                        else:
                            tuvo_conflicto = await _aplicar_variables(
                                tenant_id,
                                importacion_id,
                                contacto,
                                variables_nuevas,
                                politica,
                                contacto_repository,
                                conflicto_repository,
                            )
                            if tuvo_conflicto:
                                con_advertencia += 1
                        aceptadas += 1

                    if indice % _CONTADOR_COMMIT_CADA == 0:
                        importacion.filas_aceptadas = aceptadas
                        importacion.filas_rechazadas = rechazadas
                        importacion.filas_con_advertencia = con_advertencia
                        await importacion_repository.update(importacion)
                        await session.commit()

                importacion.filas_aceptadas = aceptadas
                importacion.filas_rechazadas = rechazadas
                importacion.filas_con_advertencia = con_advertencia
                importacion.estado = EstadoImportacion.completada
                await importacion_repository.update(importacion)
                await session.commit()
            except Exception as error:
                importacion.estado = EstadoImportacion.fallida
                importacion.motivo_fallo = str(error)[:500]
                await importacion_repository.update(importacion)
                await session.commit()
                raise
