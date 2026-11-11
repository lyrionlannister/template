import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { ParametroComercial } from "../types/parametro-comercial";

export const useParametrosComerciales = () => {
  const { apiClient } = useApiClient();

  const registrar = useCallback(
    (datos: { clave: string; valor: string; fuente: string; vigenteDesde: string }) =>
      apiClient<ParametroComercial>("/app-platform/parametros-comerciales", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const historico = useCallback(
    (clave: string) =>
      apiClient<ParametroComercial[]>(`/app-platform/parametros-comerciales/historico?clave=${encodeURIComponent(clave)}`),
    [apiClient],
  );

  const vigente = useCallback(
    (clave: string) =>
      apiClient<ParametroComercial | null>(
        `/app-platform/parametros-comerciales/vigente?clave=${encodeURIComponent(clave)}`,
      ),
    [apiClient],
  );

  return { registrar, historico, vigente };
};
