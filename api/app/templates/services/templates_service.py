"""Lógica de negocio de Plantillas: crear, consultar, editar, eliminar,
renderizar de prueba y verificar variables faltantes sobre una audiencia.

Nunca construye SQL de contactos ni de audiencias directo -- todo eso vive
en `ContactsService`/`AudienciasService` (cross-domain permitido vía
servicios, nunca vía `repositories`/`models`, ver `.importlinter`)."""

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.audiences.exceptions import AudienciaNoEncontradaError
from app.audiences.services.audiencias_service import AudienciasService
from app.contacts.exceptions import ContactoNoEncontradoError
from app.contacts.services.contacts_service import ContactsService
from app.templates.exceptions import (
    AudienciaNoEncontradaParaVerificarError,
    CategoriaRequeridaError,
    ContactoNoEncontradoParaRenderizarError,
    NombrePlantillaMetaRequeridoError,
    PlantillaNoEncontradaError,
    VariableFaltanteEnRenderizadoError,
    VariableNoPermitidaError,
)
from app.templates.models.plantilla_model import Plantilla
from app.templates.repositories.plantilla_repository import PlantillaRepository

_PATRON_VARIABLE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
CAMPO_BASE_PLANTILLA = "telefono"
_CATEGORIAS_PERMITIDAS_WHATSAPP = {CategoriaMensaje.marketing, CategoriaMensaje.utility}


class TemplatesService:
    def __init__(
        self,
        session: AsyncSession,
        plantilla_repository: PlantillaRepository,
        contacts_service: ContactsService,
        audiencias_service: AudienciasService,
    ):
        self.session = session
        self.plantilla_repository = plantilla_repository
        self.contacts_service = contacts_service
        self.audiencias_service = audiencias_service

    @staticmethod
    def _extraer_variables(contenido: str) -> list[str]:
        vistas: list[str] = []
        for clave in _PATRON_VARIABLE.findall(contenido):
            if clave not in vistas:
                vistas.append(clave)
        return vistas

    async def _validar_variables(self, variables: list[str]) -> None:
        if not variables:
            return
        claves_disponibles = set(await self.contacts_service.listar_claves_variables())
        permitidas = {CAMPO_BASE_PLANTILLA} | claves_disponibles
        no_permitidas = [v for v in variables if v not in permitidas]
        if no_permitidas:
            raise VariableNoPermitidaError(
                "Estas variables no existen como campo base ni como clave de "
                f"los contactos de esta organización: {', '.join(no_permitidas)}."
            )

    @staticmethod
    def _validar_whatsapp(
        canal: CanalMensajeria,
        categoria: CategoriaMensaje | None,
        nombre_plantilla_meta: str | None,
    ) -> tuple[CategoriaMensaje | None, str | None]:
        if canal != CanalMensajeria.whatsapp:
            return None, None
        if categoria is None or categoria not in _CATEGORIAS_PERMITIDAS_WHATSAPP:
            raise CategoriaRequeridaError(
                "Una plantilla de WhatsApp necesita categoría marketing o utility."
            )
        if not nombre_plantilla_meta:
            raise NombrePlantillaMetaRequeridoError(
                "Una plantilla de WhatsApp necesita el nombre de la plantilla "
                "aprobada en la cuenta de WhatsApp Business del cliente."
            )
        return categoria, nombre_plantilla_meta

    async def crear(
        self,
        tenant_id: int,
        nombre: str,
        canal: CanalMensajeria,
        contenido: str,
        categoria: CategoriaMensaje | None,
        nombre_plantilla_meta: str | None,
    ) -> Plantilla:
        variables = self._extraer_variables(contenido)
        await self._validar_variables(variables)
        categoria, nombre_plantilla_meta = self._validar_whatsapp(
            canal, categoria, nombre_plantilla_meta
        )
        plantilla = Plantilla(
            tenant_id=tenant_id,
            nombre=nombre,
            canal=canal,
            contenido=contenido,
            variables=variables,
            categoria=categoria,
            nombre_plantilla_meta=nombre_plantilla_meta,
        )
        plantilla = await self.plantilla_repository.add(plantilla)
        await self.session.commit()
        return plantilla

    async def obtener(self, public_id: UUID) -> Plantilla:
        plantilla = await self.plantilla_repository.obtener_por_public_id(public_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(
                "La plantilla no existe o no pertenece a esta organización."
            )
        return plantilla

    async def listar(self, pagina: int, por_pagina: int) -> tuple[list[Plantilla], int]:
        total = await self.plantilla_repository.contar_total()
        plantillas = await self.plantilla_repository.listar(
            por_pagina, (pagina - 1) * por_pagina
        )
        return plantillas, total

    async def actualizar(
        self,
        public_id: UUID,
        nombre: str | None,
        contenido: str | None,
        categoria: CategoriaMensaje | None,
        nombre_plantilla_meta: str | None,
    ) -> Plantilla:
        plantilla = await self.obtener(public_id)
        if contenido is not None:
            variables = self._extraer_variables(contenido)
            await self._validar_variables(variables)
            plantilla.contenido = contenido
            plantilla.variables = variables
        if nombre is not None:
            plantilla.nombre = nombre
        if plantilla.canal == CanalMensajeria.whatsapp:
            nueva_categoria = (
                categoria if categoria is not None else plantilla.categoria
            )
            nuevo_nombre_meta = (
                nombre_plantilla_meta
                if nombre_plantilla_meta is not None
                else plantilla.nombre_plantilla_meta
            )
            nueva_categoria, nuevo_nombre_meta = self._validar_whatsapp(
                plantilla.canal, nueva_categoria, nuevo_nombre_meta
            )
            plantilla.categoria = nueva_categoria
            plantilla.nombre_plantilla_meta = nuevo_nombre_meta
        plantilla = await self.plantilla_repository.update(plantilla)
        await self.session.commit()
        return plantilla

    async def eliminar(self, public_id: UUID) -> None:
        plantilla = await self.obtener(public_id)
        await self.plantilla_repository.delete(plantilla)
        await self.session.commit()

    async def renderizar(self, public_id: UUID, contacto_public_id: UUID) -> str:
        plantilla = await self.obtener(public_id)
        try:
            contacto = await self.contacts_service.obtener_contacto(contacto_public_id)
        except ContactoNoEncontradoError as error:
            raise ContactoNoEncontradoParaRenderizarError(str(error)) from error

        datos = {CAMPO_BASE_PLANTILLA: contacto.telefono, **contacto.variables}
        faltantes = [v for v in plantilla.variables if v not in datos or datos[v] == ""]
        if faltantes:
            raise VariableFaltanteEnRenderizadoError(
                "Este contacto no trae valor para: " + ", ".join(faltantes) + "."
            )

        def _reemplazar(match: re.Match) -> str:
            return str(datos[match.group(1)])

        return _PATRON_VARIABLE.sub(_reemplazar, plantilla.contenido)

    async def verificar_audiencia(
        self, public_id: UUID, audiencia_public_id: UUID
    ) -> tuple[int, list[dict]]:
        plantilla = await self.obtener(public_id)
        if not plantilla.variables:
            return 0, []
        try:
            audiencia = await self.audiencias_service.obtener(audiencia_public_id)
        except AudienciaNoEncontradaError as error:
            raise AudienciaNoEncontradaParaVerificarError(str(error)) from error

        ids = await self.audiencias_service.listar_ids_de_contactos(audiencia)
        contactos = await self.contacts_service.listar_por_ids(ids)

        con_faltante = []
        for contacto in contactos:
            datos = {CAMPO_BASE_PLANTILLA: contacto.telefono, **contacto.variables}
            faltantes = [
                v for v in plantilla.variables if v not in datos or datos[v] == ""
            ]
            if faltantes:
                con_faltante.append(
                    {
                        "contacto_public_id": contacto.public_id,
                        "telefono": contacto.telefono,
                        "variables_faltantes": faltantes,
                    }
                )
        return len(contactos), con_faltante
