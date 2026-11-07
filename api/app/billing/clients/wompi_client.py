"""Cliente de la pasarela de pago (hoy, únicamente Wompi -- ver `/CLAUDE.md`
"Billing: solo Wompi"). Es el único archivo del dominio que sabe que el
proveedor concreto es Wompi; el resto de `billing` habla en términos
genéricos de pasarela (ver `EventoPagoProcesado`, `FuenteDePago`).

Contrato verificado contra la documentación oficial (docs.wompi.co, vía
Context7) el 2026-11-07, no inventado:

- Base URL: sandbox `https://sandbox.wompi.co/v1`, producción
  `https://production.wompi.co/v1`.
- `POST /payment_sources`: solo con la llave privada, solo desde el backend.
- `POST /transactions`: requiere `signature` = SHA256(reference +
  amount_in_cents + currency + integrity_secret), concatenado sin
  separadores, en ese orden.
- Checksum de webhook: SHA256(valores de `signature.properties` en orden +
  `timestamp` + secreto de eventos), comparado contra
  `signature.checksum`/`X-Event-Checksum`. `properties` es dinámico, nunca
  se asume fijo.
"""

import hashlib
from typing import Any

import httpx

from app.core.config.env_tools import get_or_default, get_or_throw

PASARELA = "wompi"

_AMBIENTE_A_BASE_URL = {
    "production": "https://production.wompi.co/v1",
    "sandbox": "https://sandbox.wompi.co/v1",
}


def _base_url() -> str:
    ambiente = get_or_default("WOMPI_AMBIENTE", "sandbox")
    if ambiente not in _AMBIENTE_A_BASE_URL:
        raise ValueError(
            f"WOMPI_AMBIENTE debe ser 'sandbox' o 'production', recibido: {ambiente!r}"
        )
    return _AMBIENTE_A_BASE_URL[ambiente]


def calcular_firma_integridad(
    reference: str, amount_in_cents: int, currency: str
) -> str:
    secreto = get_or_throw("WOMPI_INTEGRITY_SECRET")
    cadena = f"{reference}{amount_in_cents}{currency}{secreto}"
    return hashlib.sha256(cadena.encode()).hexdigest()


def verificar_checksum_evento(payload: dict[str, Any]) -> bool:
    """Reconstruye el checksum del evento y lo compara contra el recibido.
    `properties` se lee siempre del propio evento, nunca de una lista fija
    en código."""

    firma = payload.get("signature") or {}
    propiedades: list[str] = firma.get("properties") or []
    checksum_recibido: str | None = firma.get("checksum")
    timestamp = payload.get("timestamp")
    if not propiedades or checksum_recibido is None or timestamp is None:
        return False

    data = payload.get("data") or {}
    valores = []
    for ruta in propiedades:
        valor: Any = data
        for parte in ruta.split("."):
            if not isinstance(valor, dict) or parte not in valor:
                return False
            valor = valor[parte]
        valores.append(str(valor))

    secreto = get_or_throw("WOMPI_EVENTS_SECRET")
    cadena = "".join(valores) + str(timestamp) + secreto
    checksum_calculado = hashlib.sha256(cadena.encode()).hexdigest()
    return checksum_calculado.upper() == str(checksum_recibido).upper()


class WompiClient:
    def __init__(self, cliente_http: httpx.AsyncClient | None = None):
        self._cliente_propio = cliente_http is None
        self._http = cliente_http or httpx.AsyncClient(
            base_url=_base_url(), timeout=15.0
        )

    async def cerrar(self) -> None:
        if self._cliente_propio:
            await self._http.aclose()

    async def crear_fuente_de_pago(
        self,
        *,
        tipo: str,
        token: str,
        customer_email: str,
        acceptance_token: str,
        accept_personal_auth: str,
        financial_operation: str | None = None,
    ) -> dict[str, Any]:
        """`POST /payment_sources`, con la llave privada. `financial_operation`
        en `"PREAUTHORIZATION"` habilita cobro recurrente sin 3DS repetido."""

        cuerpo: dict[str, Any] = {
            "type": tipo,
            "token": token,
            "customer_email": customer_email,
            "acceptance_token": acceptance_token,
            "accept_personal_auth": accept_personal_auth,
        }
        if financial_operation is not None:
            cuerpo["financial_operation"] = financial_operation

        respuesta = await self._http.post(
            "/payment_sources",
            json=cuerpo,
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def crear_preautorizacion(
        self,
        *,
        payment_source_id: int,
        customer_email: str,
        acceptance_token: str,
        accept_personal_auth: str,
        amount_in_cents: int,
        currency: str,
    ) -> dict[str, Any]:
        """`POST /payment_sources` con `financial_operation: PREAUTHORIZATION`,
        referenciando una fuente ya tokenizada (`payment_source_id`). Crea una
        preautorización NUEVA (con su propio id) que pasa por 3DS; una vez
        queda `AVAILABLE`, ese id es el que se reusa en `crear_transaccion`
        para cobros recurrentes sin fricción."""

        respuesta = await self._http.post(
            "/payment_sources",
            json={
                "type": "CARD",
                "payment_source_id": payment_source_id,
                "customer_email": customer_email,
                "financial_operation": "PREAUTHORIZATION",
                "acceptance_token": acceptance_token,
                "accept_personal_auth": accept_personal_auth,
                "data": {"amount_in_cents": amount_in_cents, "currency": currency},
            },
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_fuente_de_pago(self, payment_source_id: int) -> dict[str, Any]:
        respuesta = await self._http.get(
            f"/payment_sources/{payment_source_id}",
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def crear_transaccion(
        self,
        *,
        reference: str,
        amount_in_cents: int,
        currency: str,
        customer_email: str,
        payment_source_id: int | None = None,
        payment_method: dict[str, Any] | None = None,
        installments: int = 1,
        acceptance_token: str | None = None,
        accept_personal_auth: str | None = None,
    ) -> dict[str, Any]:
        """`POST /transactions`. Con `payment_source_id` reusa una fuente ya
        tokenizada (onboarding, recarga con tarjeta guardada, cobro
        recurrente) -- el consentimiento ya quedó registrado al crear esa
        fuente, no hace falta de nuevo. Con `payment_method` (PSE, Nequi
        puntual) sí hace falta un `acceptance_token`/`accept_personal_auth`
        frescos (confirmado en vivo contra el sandbox: sin ellos, 422
        "acceptance_token no está presente")."""

        cuerpo: dict[str, Any] = {
            "amount_in_cents": amount_in_cents,
            "currency": currency,
            "customer_email": customer_email,
            "reference": reference,
            "public_key": get_or_throw("WOMPI_PUBLIC_KEY"),
            "signature": calcular_firma_integridad(
                reference, amount_in_cents, currency
            ),
        }
        if payment_source_id is not None:
            cuerpo["payment_source_id"] = payment_source_id
            cuerpo["payment_method"] = {"installments": installments}
        elif payment_method is not None:
            if acceptance_token is None or accept_personal_auth is None:
                raise ValueError(
                    "payment_method requiere acceptance_token y accept_personal_auth."
                )
            cuerpo["payment_method"] = payment_method
            cuerpo["acceptance_token"] = acceptance_token
            cuerpo["accept_personal_auth"] = accept_personal_auth
        else:
            raise ValueError("Se requiere payment_source_id o payment_method.")

        respuesta = await self._http.post(
            "/transactions",
            json=cuerpo,
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_tokens_de_aceptacion(self) -> dict[str, Any]:
        """`GET /merchants/info`. Se llama desde el backend, no desde el
        navegador: este endpoint exige el header `x-merchant-public-key` y
        Wompi no lo habilita para CORS (comprobado en vivo contra el
        sandbox), a diferencia de `POST /tokens/cards`, que sí está pensado
        para llamarse directo desde el cliente."""

        respuesta = await self._http.get(
            "/merchants/info",
            headers={"x-merchant-public-key": get_or_throw("WOMPI_PUBLIC_KEY")},
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_instituciones_financieras(self) -> dict[str, Any]:
        """`GET /pse/financial_institutions`: lista de bancos para PSE. Se
        llama desde el backend por el mismo motivo que `/merchants/info`."""

        respuesta = await self._http.get(
            "/pse/financial_institutions",
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_transaccion(self, transaction_id: str) -> dict[str, Any]:
        respuesta = await self._http.get(
            f"/transactions/{transaction_id}",
            headers=self._encabezado_llave_privada(),
        )
        respuesta.raise_for_status()
        return respuesta.json()

    def _encabezado_llave_privada(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {get_or_throw('WOMPI_PRIVATE_KEY')}"}
