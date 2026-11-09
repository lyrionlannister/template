"""Lógica de negocio de Audiencias: crear, consultar, editar, duplicar y
eliminar filtros guardados sobre contactos. La ejecución real del filtro
(contar, listar ids, descubrir claves) vive en `ContactsService` -- este
servicio nunca construye SQL ni toca `Contacto` directo."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audiences.enums.audiences_enums import TipoAudiencia
from app.audiences.exceptions import (
    AudienciaEstaticaInmutableError,
    AudienciaNoEncontradaError,
)
from app.audiences.models.audiencia_model import Audiencia
from app.audiences.repositories.audiencia_repository import AudienciaRepository
from app.contacts.schemas.filtro_schema import (
    CAMPOS_BASE,
    OPERADORES_VARIABLE,
    FiltroAudiencia,
)
from app.contacts.services.contacts_service import ContactsService


class AudienciasService:
    def __init__(
        self,
        session: AsyncSession,
        audiencia_repository: AudienciaRepository,
        contacts_service: ContactsService,
    ):
        self.session = session
        self.audiencia_repository = audiencia_repository
        self.contacts_service = contacts_service

    async def campos_disponibles(self) -> list[dict]:
        campos = [
            {"field": campo, "operadores": sorted(operadores)}
            for campo, operadores in CAMPOS_BASE.items()
        ]
        claves = await self.contacts_service.listar_claves_variables()
        campos += [
            {"field": f"variables.{clave}", "operadores": sorted(OPERADORES_VARIABLE)}
            for clave in claves
        ]
        return campos

    async def vista_previa(self, filtro: FiltroAudiencia) -> int:
        return await self.contacts_service.contar_por_filtro(filtro)

    async def crear(
        self, tenant_id: int, nombre: str, tipo: TipoAudiencia, filtro: FiltroAudiencia
    ) -> Audiencia:
        audiencia = Audiencia(
            tenant_id=tenant_id,
            nombre=nombre,
            tipo=tipo,
            filtro=filtro.model_dump(by_alias=True),
        )
        if tipo == TipoAudiencia.estatica:
            ids = await self.contacts_service.listar_ids_por_filtro(filtro)
            audiencia.congelada_en = datetime.now(UTC)
            audiencia = await self.audiencia_repository.add(audiencia)
            await self.audiencia_repository.guardar_snapshot(audiencia.id, ids)
        else:
            audiencia = await self.audiencia_repository.add(audiencia)
        await self.session.commit()
        return audiencia

    async def obtener(self, public_id: UUID) -> Audiencia:
        audiencia = await self.audiencia_repository.obtener_por_public_id(public_id)
        if audiencia is None:
            raise AudienciaNoEncontradaError(
                "La audiencia no existe o no pertenece a esta organización."
            )
        return audiencia

    async def listar(self, pagina: int, por_pagina: int) -> tuple[list[Audiencia], int]:
        total = await self.audiencia_repository.contar_total()
        audiencias = await self.audiencia_repository.listar(
            por_pagina, (pagina - 1) * por_pagina
        )
        return audiencias, total

    async def contar(self, audiencia: Audiencia) -> int:
        if audiencia.tipo == TipoAudiencia.dinamica:
            filtro = FiltroAudiencia.model_validate(audiencia.filtro)
            return await self.contacts_service.contar_por_filtro(filtro)
        return await self.audiencia_repository.contar_snapshot(audiencia.id)

    async def actualizar(
        self,
        public_id: UUID,
        nombre: str | None,
        filtro: FiltroAudiencia | None,
    ) -> Audiencia:
        audiencia = await self.obtener(public_id)
        if filtro is not None:
            if audiencia.tipo == TipoAudiencia.estatica:
                raise AudienciaEstaticaInmutableError(
                    "Una audiencia estática ya congeló su snapshot: su filtro "
                    "no se puede editar. Duplícala como dinámica para "
                    "usar un filtro distinto."
                )
            audiencia.filtro = filtro.model_dump(by_alias=True)
        if nombre is not None:
            audiencia.nombre = nombre
        audiencia = await self.audiencia_repository.update(audiencia)
        await self.session.commit()
        return audiencia

    async def duplicar(self, public_id: UUID, tipo: TipoAudiencia) -> Audiencia:
        original = await self.obtener(public_id)
        filtro = FiltroAudiencia.model_validate(original.filtro)
        return await self.crear(
            original.tenant_id, f"{original.nombre} (copia)", tipo, filtro
        )

    async def eliminar(self, public_id: UUID) -> None:
        audiencia = await self.obtener(public_id)
        await self.audiencia_repository.delete(audiencia)
        await self.session.commit()
