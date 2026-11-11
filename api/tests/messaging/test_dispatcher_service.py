"""Test de la garantía invariante "WhatsApp nunca por Sent.dm" (`/CLAUDE.md`).
Este test debe fallar si alguien introduce, por accidente o a propósito,
una ruta de WhatsApp hacia Sent en la tabla de enrutamiento."""

import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.messaging.services.dispatcher_service import (
    _ENRUTAMIENTO,
    CanalSinProveedorError,
    ProveedorMensajeria,
    proveedor_de,
)


def test_whatsapp_enruta_a_meta():
    assert proveedor_de(CanalMensajeria.whatsapp) == ProveedorMensajeria.meta


@pytest.mark.parametrize("canal", [CanalMensajeria.sms, CanalMensajeria.rcs])
def test_sms_y_rcs_no_tienen_proveedor_todavia(canal):
    with pytest.raises(CanalSinProveedorError):
        proveedor_de(canal)


def test_ningun_canal_enruta_a_sent():
    """Ni siquiera estructuralmente: "sent" no es un valor posible del
    enum `ProveedorMensajeria`, así que ningún valor de la tabla puede
    apuntar ahí. Si alguien agrega esa opción y la enruta, este test lo
    detecta."""
    valores_enrutados = {p.value for p in _ENRUTAMIENTO.values() if p is not None}
    assert "sent" not in valores_enrutados
    assert valores_enrutados == {"meta"}
