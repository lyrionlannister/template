import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { TipoCambio } from "../types/tipo-cambio";

export const useTipoCambio = () => {
  const { apiClient } = useApiClient();

  const registrar = useCallback(
    (datos: { par: string; valor: string; fuente: string; vigenteDesde: string }) =>
      apiClient<TipoCambio>("/app-platform/tipo-cambio", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const historico = useCallback(
    (par: string) => apiClient<TipoCambio[]>(`/app-platform/tipo-cambio/historico?par=${encodeURIComponent(par)}`),
    [apiClient],
  );

  const vigente = useCallback(
    (par: string) => apiClient<TipoCambio | null>(`/app-platform/tipo-cambio/vigente?par=${encodeURIComponent(par)}`),
    [apiClient],
  );

  return { registrar, historico, vigente };
};
