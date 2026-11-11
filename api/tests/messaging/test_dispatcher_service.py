"""Test de la garantía invariante "WhatsApp nunca por Sent.dm" (`/CLAUDE.md`).
Este test debe fallar si alguien introduce, por accidente o a propósito,
una ruta de WhatsApp hacia Sent en la tabla de enrutamiento."""

import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.messaging.services.dispatcher_service import (
    _ENRUTAMIENTO,
    ProveedorMensajeria,
    proveedor_de,
)


def test_whatsapp_enruta_a_meta():
    assert proveedor_de(CanalMensajeria.whatsapp) == ProveedorMensajeria.meta


@pytest.mark.parametrize("canal", [CanalMensajeria.sms, CanalMensajeria.rcs])
def test_sms_y_rcs_enrutan_a_sent(canal):
    assert proveedor_de(canal) == ProveedorMensajeria.sent


def test_whatsapp_nunca_enruta_a_sent():
    """Estructural, no solo de comportamiento: si alguien cambia la entrada
    de `whatsapp` en `_ENRUTAMIENTO` a `sent`, este test lo detecta sin
    necesitar que nadie primero intente enviar un mensaje."""
    assert _ENRUTAMIENTO[CanalMensajeria.whatsapp] is ProveedorMensajeria.meta
    assert _ENRUTAMIENTO[CanalMensajeria.whatsapp] is not ProveedorMensajeria.sent
