import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { CanalMensajeria, CategoriaMensaje, CostoCanal } from "../types/costo-canal";

export const useCostosCanal = () => {
  const { apiClient } = useApiClient();

  const registrar = useCallback(
    (datos: {
      canal: CanalMensajeria;
      categoria: CategoriaMensaje | null;
      proveedor: string;
      costoUnitario: string;
      moneda: string;
      vigenteDesde: string;
      fuente: string;
    }) =>
      apiClient<CostoCanal>("/app-platform/costos", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const historico = useCallback(
    (canal: CanalMensajeria, categoria?: CategoriaMensaje) => {
      const params = new URLSearchParams({ canal });
      if (categoria) params.set("categoria", categoria);
      return apiClient<CostoCanal[]>(`/app-platform/costos/historico?${params.toString()}`);
    },
    [apiClient],
  );

  const vigente = useCallback(
    (canal: CanalMensajeria, categoria?: CategoriaMensaje) => {
      const params = new URLSearchParams({ canal });
      if (categoria) params.set("categoria", categoria);
      return apiClient<CostoCanal | null>(`/app-platform/costos/vigente?${params.toString()}`);
    },
    [apiClient],
  );

  return { registrar, historico, vigente };
};
