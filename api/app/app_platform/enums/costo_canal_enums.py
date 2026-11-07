"""Enumeraciones de canal y categoría de mensaje, compartidas por modelo,
repository, service, schema y controller del histórico de costos."""

import enum


class CanalMensajeria(enum.StrEnum):
    whatsapp = "whatsapp"
    sms = "sms"
    rcs = "rcs"


class CategoriaMensaje(enum.StrEnum):
    marketing = "marketing"
    utility = "utility"
    authentication = "authentication"
    service = "service"
