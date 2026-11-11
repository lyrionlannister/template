from datetime import datetime
from uuid import UUID

from app.core.schemas.base_schema import BaseSchema


class ConectarWhatsappRequest(BaseSchema):
    code: str
    waba_id: str
    phone_number_id: str


class ConexionWhatsappRespuesta(BaseSchema):
    public_id: UUID
    waba_id: str
    phone_number_id: str
    numero_telefono: str
    creado_en: datetime


class EnviarPlantillaRequest(BaseSchema):
    plantilla_public_id: UUID
    contacto_public_id: UUID


class EnvioPlantillaRespuesta(BaseSchema):
    message_id: str


class PlantillaOtpPlataformaCrearRequest(BaseSchema):
    nombre: str
    idioma: str


class PlantillaOtpPlataformaRespuesta(BaseSchema):
    public_id: UUID
    nombre: str
    idioma: str
    estado_meta: str
    creado_en: datetime
