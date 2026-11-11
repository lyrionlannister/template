"""Envío real de un mensaje de plantilla. No descuenta saldo ni pool de
incluidos -- eso vive en `app_platform`/`billing`, se conecta cuando
exista `campaigns` (fase 10 de `/CLAUDE.md`). No procesa webhooks de
estado de entrega -- dominio `delivery`, no existe todavía."""

from uuid import UUID

from app.contacts.services.contacts_service import ContactsService
from app.core.security import credenciales_cipher
from app.messaging.clients.meta_client import MetaClient
from app.messaging.exceptions import VariableFaltanteParaEnvioError
from app.messaging.services.conexion_whatsapp_service import ConexionWhatsappService
from app.messaging.services.dispatcher_service import proveedor_de
from app.templates.services.templates_service import (
    CAMPO_BASE_PLANTILLA,
    TemplatesService,
)

_IDIOMA_PLANTILLA_DEFAULT = "es_CO"


class EnvioMensajeService:
    def __init__(
        self,
        conexion_service: ConexionWhatsappService,
        templates_service: TemplatesService,
        contacts_service: ContactsService,
        meta_client: MetaClient,
    ):
        self.conexion_service = conexion_service
        self.templates_service = templates_service
        self.contacts_service = contacts_service
        self.meta_client = meta_client

    async def enviar_plantilla(
        self, plantilla_public_id: UUID, contacto_public_id: UUID
    ) -> dict:
        plantilla = await self.templates_service.obtener(plantilla_public_id)
        # Pasa por el dispatcher aunque hoy solo WhatsApp llegue aquí: es la
        # garantía "WhatsApp nunca por Sent.dm" aplicada también en el punto
        # de envío, no solo en la tabla de enrutamiento.
        proveedor_de(plantilla.canal)

        contacto = await self.contacts_service.obtener_contacto(contacto_public_id)
        datos = {CAMPO_BASE_PLANTILLA: contacto.telefono, **contacto.variables}
        faltantes = [v for v in plantilla.variables if v not in datos or datos[v] == ""]
        if faltantes:
            raise VariableFaltanteParaEnvioError(
                "Este contacto no trae valor para: " + ", ".join(faltantes) + "."
            )

        # El orden de `plantilla.variables` es el orden de primera aparición
        # en el contenido (ver `TemplatesService._extraer_variables`): ESE
        # orden es el índice {{1}}, {{2}}... de Meta, sin reordenar.
        parametros_posicionales = [
            str(datos[variable]) for variable in plantilla.variables
        ]

        conexion = await self.conexion_service.obtener_para_envio()
        token_acceso = credenciales_cipher.descifrar(conexion.token_acceso_cifrado)

        return await self.meta_client.enviar_plantilla(
            phone_number_id=conexion.phone_number_id,
            token_acceso=token_acceso,
            telefono_destino=contacto.telefono,
            nombre_plantilla=plantilla.nombre_plantilla_meta,
            idioma=_IDIOMA_PLANTILLA_DEFAULT,
            parametros_posicionales=parametros_posicionales,
        )
