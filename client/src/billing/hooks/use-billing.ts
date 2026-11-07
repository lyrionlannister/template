import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { Cobro } from "../types/cobro";
import type { OnboardingEstado } from "../types/onboarding-estado";

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

  return { obtenerEstadoOnboarding, pagarOnboarding };
};
