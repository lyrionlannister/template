import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { ConexionWhatsapp, EnvioPlantillaResultado } from "../types/conexion-whatsapp";

export const useMessaging = () => {
  const { apiClient } = useApiClient();

  const conectarWhatsapp = useCallback(
    (datos: { code: string; wabaId: string; phoneNumberId: string }) =>
      apiClient<ConexionWhatsapp>("/messaging/whatsapp/conectar", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const enviarPlantilla = useCallback(
    (datos: { plantillaPublicId: string; contactoPublicId: string }) =>
      apiClient<EnvioPlantillaResultado>("/messaging/plantillas/enviar", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  return { conectarWhatsapp, enviarPlantilla };
};
