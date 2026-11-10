import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type {
  CanalMensajeria,
  CategoriaMensaje,
  Plantilla,
  PlantillasPaginadas,
  VerificarAudienciaResultado,
} from "../types/plantilla";

export const useTemplates = () => {
  const { apiClient } = useApiClient();

  const listarPlantillas = useCallback(
    (pagina: number, porPagina: number) =>
      apiClient<PlantillasPaginadas>(`/templates?pagina=${pagina}&porPagina=${porPagina}`),
    [apiClient],
  );

  const obtenerPlantilla = useCallback(
    (publicId: string) => apiClient<Plantilla>(`/templates/${publicId}`),
    [apiClient],
  );

  const crearPlantilla = useCallback(
    (datos: {
      nombre: string;
      canal: CanalMensajeria;
      contenido: string;
      categoria?: CategoriaMensaje | null;
      nombrePlantillaMeta?: string | null;
    }) =>
      apiClient<Plantilla>("/templates", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const actualizarPlantilla = useCallback(
    (
      publicId: string,
      cambios: {
        nombre?: string;
        contenido?: string;
        categoria?: CategoriaMensaje | null;
        nombrePlantillaMeta?: string | null;
      },
    ) =>
      apiClient<Plantilla>(`/templates/${publicId}`, {
        method: "PATCH",
        body: JSON.stringify(cambios),
      }),
    [apiClient],
  );

  const eliminarPlantilla = useCallback(
    (publicId: string) => apiClient<null>(`/templates/${publicId}`, { method: "DELETE" }),
    [apiClient],
  );

  const renderizarPlantilla = useCallback(
    (publicId: string, contactoPublicId: string) =>
      apiClient<{ texto: string }>(`/templates/${publicId}/renderizar`, {
        method: "POST",
        body: JSON.stringify({ contactoPublicId }),
      }).then((r) => r.texto),
    [apiClient],
  );

  const verificarAudiencia = useCallback(
    (publicId: string, audienciaPublicId: string) =>
      apiClient<VerificarAudienciaResultado>(`/templates/${publicId}/verificar-audiencia`, {
        method: "POST",
        body: JSON.stringify({ audienciaPublicId }),
      }),
    [apiClient],
  );

  return {
    listarPlantillas,
    obtenerPlantilla,
    crearPlantilla,
    actualizarPlantilla,
    eliminarPlantilla,
    renderizarPlantilla,
    verificarAudiencia,
  };
};
