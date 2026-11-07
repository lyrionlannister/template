"""Endpoint de webhooks de la pasarela de pago. Público por diseño (la
verificación es el checksum, no una sesión): ningún navegador lo llama, así
que no exige autenticación ni CSRF. El cuerpo se lee como JSON crudo, no como
un schema Pydantic estricto -- la doc de la pasarela advierte que las
propiedades firmadas varían por evento y con el tiempo (ver `wompi_client`)."""

from fastapi import APIRouter, HTTPException, Request, status

from app.billing.dependencies import EventoPagoServiceDep
from app.billing.exceptions import ChecksumInvalidoError

router = APIRouter(prefix="/billing/webhooks", tags=["billing"])


@router.post("/wompi", status_code=status.HTTP_200_OK)
async def recibir_evento_wompi(
    request: Request, service: EventoPagoServiceDep
) -> dict[str, str]:
    payload = await request.json()
    try:
        await service.procesar_webhook(payload)
    except ChecksumInvalidoError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error
    return {"status": "ok"}
