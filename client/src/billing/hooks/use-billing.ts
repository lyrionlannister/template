import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { Cobro } from "../types/cobro";
import type {
  EstadoFuenteDePagoPolling,
  FuenteDePago,
  TokensDeAceptacion,
} from "../types/fuente-de-pago";
import type { OnboardingEstado } from "../types/onboarding-estado";
import type {
  InstitucionFinanciera,
  MovimientoSaldo,
  RecargaPseResultado,
  SaldoEstado,
} from "../types/saldo";
import type { SuscripcionEstado } from "../types/suscripcion-estado";

export const useBilling = () => {
  const { apiClient } = useApiClient();

  const obtenerEstadoOnboarding = useCallback(
    () => apiClient<OnboardingEstado>("/billing/onboarding/estado"),
    [apiClient],
  );

  const pagarOnboarding = useCallback(
    (datos: { token: string; acceptanceToken: string; acceptPersonalAuth: string }) =>
      apiClient<Cobro>("/billing/onboarding", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const obtenerTokensDeAceptacion = useCallback(
    () => apiClient<TokensDeAceptacion>("/billing/tokens-aceptacion"),
    [apiClient],
  );

  const iniciarFuenteDePago = useCallback(
    (datos: {
      token: string;
      acceptanceToken: string;
      acceptPersonalAuth: string;
      marca?: string;
      ultimosCuatro?: string;
      mesExpiracion?: string;
      anioExpiracion?: string;
      titular?: string;
    }) =>
      apiClient<FuenteDePago>("/billing/fuentes-de-pago", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const consultarEstadoFuenteDePago = useCallback(
    (publicId: string) =>
      apiClient<EstadoFuenteDePagoPolling>(`/billing/fuentes-de-pago/${publicId}/estado`),
    [apiClient],
  );

  const obtenerEstadoSuscripcion = useCallback(
    () => apiClient<SuscripcionEstado>("/billing/suscripcion/estado"),
    [apiClient],
  );

  const obtenerEstadoSaldo = useCallback(
    () => apiClient<SaldoEstado>("/billing/saldo/estado"),
    [apiClient],
  );

  const obtenerInstitucionesFinancieras = useCallback(
    () => apiClient<InstitucionFinanciera[]>("/billing/saldo/instituciones-financieras"),
    [apiClient],
  );

  const consultarEstadoMovimiento = useCallback(
    (publicId: string) =>
      apiClient<MovimientoSaldo>(`/billing/saldo/movimientos/${publicId}/estado`),
    [apiClient],
  );

  const recargarTarjeta = useCallback(
    (datos: {
      montoCop: number;
      token: string;
      acceptanceToken: string;
      acceptPersonalAuth: string;
    }) =>
      apiClient<MovimientoSaldo>("/billing/saldo/recargar/tarjeta", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const recargarPse = useCallback(
    (datos: {
      montoCop: number;
      userType: number;
      userLegalIdType: string;
      userLegalId: string;
      financialInstitutionCode: string;
    }) =>
      apiClient<RecargaPseResultado>("/billing/saldo/recargar/pse", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const recargarNequi = useCallback(
    (datos: { montoCop: number; phoneNumber: string }) =>
      apiClient<MovimientoSaldo>("/billing/saldo/recargar/nequi", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  return {
    obtenerEstadoOnboarding,
    pagarOnboarding,
    obtenerTokensDeAceptacion,
    iniciarFuenteDePago,
    consultarEstadoFuenteDePago,
    obtenerEstadoSuscripcion,
    obtenerEstadoSaldo,
    obtenerInstitucionesFinancieras,
    consultarEstadoMovimiento,
    recargarTarjeta,
    recargarPse,
    recargarNequi,
  };
};
