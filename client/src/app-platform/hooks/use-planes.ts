import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { Plan, PlanRequest } from "../types/plan";

export const usePlanes = () => {
  const { apiClient } = useApiClient();

  const listarPlanes = useCallback(() => apiClient<Plan[]>("/app-platform/planes"), [apiClient]);

  const crearPlan = useCallback(
    (datos: PlanRequest) =>
      apiClient<Plan>("/app-platform/planes", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const actualizarPlan = useCallback(
    (publicId: string, cambios: Partial<PlanRequest>) =>
      apiClient<Plan>(`/app-platform/planes/${publicId}`, {
        method: "PATCH",
        body: JSON.stringify(cambios),
      }),
    [apiClient],
  );

  return { listarPlanes, crearPlan, actualizarPlan };
};
