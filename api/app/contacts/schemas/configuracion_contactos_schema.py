"""Schemas de configuración de contactos y de conflictos de variables."""

from datetime import datetime
from uuid import UUID

from app.contacts.enums.contacts_enums import PoliticaConflictoVariables
from app.core.schemas.base_schema import BaseSchema


class ConfiguracionContactosRespuesta(BaseSchema):
    politica_conflicto_variables: PoliticaConflictoVariables


class ActualizarConfiguracionContactosRequest(BaseSchema):
    politica_conflicto_variables: PoliticaConflictoVariables


class ConflictoVariableRespuesta(BaseSchema):
    public_id: UUID
    clave: str
    valor_anterior: str
    valor_nuevo: str
    revertido_en: datetime | None
    creado_en: datetime


class RevertirConflictoRespuesta(BaseSchema):
    estado: str
