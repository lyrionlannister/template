import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { PlantillaOtpPlataforma } from "../types/plantilla-otp-plataforma";

export const usePlantillaOtpPlataforma = () => {
  const { apiClient } = useApiClient();

  const listar = useCallback(
    () => apiClient<PlantillaOtpPlataforma[]>("/messaging/plataforma/plantilla-otp"),
    [apiClient],
  );

  const crear = useCallback(
    (nombre: string, idioma: string) =>
      apiClient<PlantillaOtpPlataforma>("/messaging/plataforma/plantilla-otp", {
        method: "POST",
        body: JSON.stringify({ nombre, idioma }),
      }),
    [apiClient],
  );

  const sincronizar = useCallback(
    (publicId: string) =>
      apiClient<PlantillaOtpPlataforma>(`/messaging/plataforma/plantilla-otp/${publicId}/sincronizar`, {
        method: "POST",
      }),
    [apiClient],
  );

  return { listar, crear, sincronizar };
};
