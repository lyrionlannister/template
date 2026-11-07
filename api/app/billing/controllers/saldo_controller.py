"""Recarga y consulta de saldo utilizable (SMS/RCS)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import SesionActual
from app.billing.dependencies import MovimientoSaldoServiceDep, WompiClientDep
from app.billing.schemas.saldo_schema import (
    InstitucionFinancieraRespuesta,
    MovimientoSaldoRespuesta,
    RecargaPseRespuesta,
    RecargarNequiRequest,
    RecargarPseRequest,
    RecargarTarjetaRequest,
    SaldoEstadoRespuesta,
)
from app.billing.services.movimiento_saldo_service import (
    MovimientoSaldoNoEncontradoError,
)

router = APIRouter(prefix="/billing/saldo", tags=["billing"])


def _a_respuesta(movimiento) -> MovimientoSaldoRespuesta:
    return MovimientoSaldoRespuesta(
        public_id=movimiento.public_id,
        estado=movimiento.estado.value,
        medio=movimiento.medio.value if movimiento.medio else None,
        monto_cop=movimiento.monto_cop,
        referencia=movimiento.referencia,
    )


@router.get(
    "/instituciones-financieras", response_model=list[InstitucionFinancieraRespuesta]
)
async def instituciones_financieras(
    _sesion: SesionActual, wompi_client: WompiClientDep
) -> list[InstitucionFinancieraRespuesta]:
    datos = await wompi_client.obtener_instituciones_financieras()
    return [
        InstitucionFinancieraRespuesta(
            code=i["financial_institution_code"], name=i["financial_institution_name"]
        )
        for i in datos["data"]
    ]


@router.get("/estado", response_model=SaldoEstadoRespuesta)
async def estado_saldo(
    _sesion: SesionActual, service: MovimientoSaldoServiceDep
) -> SaldoEstadoRespuesta:
    saldo = await service.calcular_saldo()
    movimientos = await service.listar_movimientos()
    return SaldoEstadoRespuesta(
        saldo_cop=saldo, movimientos=[_a_respuesta(m) for m in movimientos]
    )


@router.get("/movimientos/{public_id}/estado", response_model=MovimientoSaldoRespuesta)
async def estado_movimiento(
    public_id: UUID, _sesion: SesionActual, service: MovimientoSaldoServiceDep
) -> MovimientoSaldoRespuesta:
    try:
        movimiento = await service.consultar_estado_movimiento(public_id)
    except MovimientoSaldoNoEncontradoError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return _a_respuesta(movimiento)


@router.post(
    "/recargar/tarjeta",
    response_model=MovimientoSaldoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def recargar_tarjeta(
    body: RecargarTarjetaRequest,
    sesion: SesionActual,
    service: MovimientoSaldoServiceDep,
) -> MovimientoSaldoRespuesta:
    movimiento = await service.recargar_tarjeta(
        sesion,
        body.monto_cop,
        body.token,
        body.acceptance_token,
        body.accept_personal_auth,
    )
    return _a_respuesta(movimiento)


@router.post(
    "/recargar/pse",
    response_model=RecargaPseRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def recargar_pse(
    body: RecargarPseRequest, sesion: SesionActual, service: MovimientoSaldoServiceDep
) -> RecargaPseRespuesta:
    movimiento, url = await service.recargar_pse(
        sesion,
        body.monto_cop,
        body.user_type,
        body.user_legal_id_type,
        body.user_legal_id,
        body.financial_institution_code,
    )
    return RecargaPseRespuesta(
        movimiento=_a_respuesta(movimiento), async_payment_url=url
    )


@router.post(
    "/recargar/nequi",
    response_model=MovimientoSaldoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def recargar_nequi(
    body: RecargarNequiRequest, sesion: SesionActual, service: MovimientoSaldoServiceDep
) -> MovimientoSaldoRespuesta:
    movimiento = await service.recargar_nequi(sesion, body.monto_cop, body.phone_number)
    return _a_respuesta(movimiento)
