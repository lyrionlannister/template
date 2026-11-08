import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { ConflictoVariable } from "../types/conflicto";
import type { ConfiguracionContactos, PoliticaConflictoVariables } from "../types/configuracion";
import type { Contacto, ContactosPaginados } from "../types/contacto";
import type {
  EstadoImportacionDetalle,
  ImportacionContacto,
  PrevisualizacionImportacion,
  RechazosPaginados,
} from "../types/importacion";

export const useContacts = () => {
  const { apiClient } = useApiClient();

  const previsualizarImportacion = useCallback(
    (archivo: File) => {
      const body = new FormData();
      body.append("archivo", archivo);
      return apiClient<PrevisualizacionImportacion>("/contacts/importaciones/previsualizar", {
        method: "POST",
        body,
      });
    },
    [apiClient],
  );

  const confirmarImportacion = useCallback(
    (datos: { previewId: string; columnaTelefono: string; mapeoVariables: Record<string, string> }) =>
      apiClient<ImportacionContacto>("/contacts/importaciones", {
        method: "POST",
        body: JSON.stringify(datos),
      }),
    [apiClient],
  );

  const obtenerEstadoImportacion = useCallback(
    (publicId: string) => apiClient<EstadoImportacionDetalle>(`/contacts/importaciones/${publicId}`),
    [apiClient],
  );

  const listarRechazosDeImportacion = useCallback(
    (publicId: string, pagina: number, porPagina: number) =>
      apiClient<RechazosPaginados>(
        `/contacts/importaciones/${publicId}/rechazos?pagina=${pagina}&porPagina=${porPagina}`,
      ),
    [apiClient],
  );

  const listarContactos = useCallback(
    (pagina: number, porPagina: number, telefono: string) => {
      const query = new URLSearchParams({ pagina: String(pagina), porPagina: String(porPagina) });
      if (telefono) query.set("telefono", telefono);
      return apiClient<ContactosPaginados>(`/contacts/contactos?${query.toString()}`);
    },
    [apiClient],
  );

  const obtenerContacto = useCallback(
    (publicId: string) => apiClient<Contacto>(`/contacts/contactos/${publicId}`),
    [apiClient],
  );

  const obtenerConfiguracion = useCallback(
    () => apiClient<ConfiguracionContactos>("/contacts/configuracion"),
    [apiClient],
  );

  const actualizarConfiguracion = useCallback(
    (politicaConflictoVariables: PoliticaConflictoVariables) =>
      apiClient<ConfiguracionContactos>("/contacts/configuracion", {
        method: "PUT",
        body: JSON.stringify({ politicaConflictoVariables }),
      }),
    [apiClient],
  );

  const listarConflictosDeContacto = useCallback(
    (contactoPublicId: string) =>
      apiClient<ConflictoVariable[]>(`/contacts/contactos/${contactoPublicId}/conflictos`),
    [apiClient],
  );

  const revertirConflicto = useCallback(
    (conflictoPublicId: string) =>
      apiClient<{ estado: string }>(`/contacts/conflictos/${conflictoPublicId}/revertir`, {
        method: "POST",
      }),
    [apiClient],
  );

  return {
    previsualizarImportacion,
    confirmarImportacion,
    obtenerEstadoImportacion,
    listarRechazosDeImportacion,
    listarContactos,
    obtenerContacto,
    obtenerConfiguracion,
    actualizarConfiguracion,
    listarConflictosDeContacto,
    revertirConflicto,
  };
};
