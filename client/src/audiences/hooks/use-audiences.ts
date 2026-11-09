import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { Audiencia, AudienciasPaginadas, TipoAudiencia } from "../types/audiencia";
import type { CampoFiltro, FiltroAudiencia } from "../types/filtro";

export const useAudiences = () => {
  const { apiClient } = useApiClient();

  const camposDisponibles = useCallback(
    () => apiClient<{ campos: CampoFiltro[] }>("/audiences/campos").then((r) => r.campos),
    [apiClient],
  );

  const vistaPrevia = useCallback(
    (filtro: FiltroAudiencia) =>
      apiClient<{ conteo: number }>("/audiences/vista-previa", {
        method: "POST",
        body: JSON.stringify({ filtro }),
      }).then((r) => r.conteo),
    [apiClient],
  );

  const listarAudiencias = useCallback(
    (pagina: number, porPagina: number) =>
      apiClient<AudienciasPaginadas>(`/audiences?pagina=${pagina}&porPagina=${porPagina}`),
    [apiClient],
  );

  const obtenerAudiencia = useCallback(
    (publicId: string) => apiClient<Audiencia>(`/audiences/${publicId}`),
    [apiClient],
  );

  const crearAudiencia = useCallback(
    (nombre: string, tipo: TipoAudiencia, filtro: FiltroAudiencia) =>
      apiClient<Audiencia>("/audiences", {
        method: "POST",
        body: JSON.stringify({ nombre, tipo, filtro }),
      }),
    [apiClient],
  );

  const actualizarAudiencia = useCallback(
    (publicId: string, cambios: { nombre?: string; filtro?: FiltroAudiencia }) =>
      apiClient<Audiencia>(`/audiences/${publicId}`, {
        method: "PATCH",
        body: JSON.stringify(cambios),
      }),
    [apiClient],
  );

  const duplicarAudiencia = useCallback(
    (publicId: string, tipo: TipoAudiencia) =>
      apiClient<Audiencia>(`/audiences/${publicId}/duplicar`, {
        method: "POST",
        body: JSON.stringify({ tipo }),
      }),
    [apiClient],
  );

  const eliminarAudiencia = useCallback(
    (publicId: string) => apiClient<null>(`/audiences/${publicId}`, { method: "DELETE" }),
    [apiClient],
  );

  return {
    camposDisponibles,
    vistaPrevia,
    listarAudiencias,
    obtenerAudiencia,
    crearAudiencia,
    actualizarAudiencia,
    duplicarAudiencia,
    eliminarAudiencia,
  };
};
