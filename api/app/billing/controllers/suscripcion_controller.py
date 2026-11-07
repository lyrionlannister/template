"""Estado de la suscripción mensual del tenant."""

from fastapi import APIRouter

from app.auth.dependencies import SesionActual
from app.billing.dependencies import SuscripcionServiceDep
from app.billing.schemas.suscripcion_schema import SuscripcionEstadoRespuesta

router = APIRouter(prefix="/billing/suscripcion", tags=["billing"])


@router.get("/estado", response_model=SuscripcionEstadoRespuesta)
async def estado_suscripcion(
    _sesion: SesionActual, service: SuscripcionServiceDep
) -> SuscripcionEstadoRespuesta:
    suscripcion = await service.consultar_estado()
    if suscripcion is None:
        return SuscripcionEstadoRespuesta(
            existe=False, estado=None, monto_cop=None, proxima_fecha_cobro=None
        )
    return SuscripcionEstadoRespuesta(
        existe=True,
        estado=suscripcion.estado.value,
        monto_cop=suscripcion.monto_cop,
        proxima_fecha_cobro=suscripcion.proxima_fecha_cobro,
    )
