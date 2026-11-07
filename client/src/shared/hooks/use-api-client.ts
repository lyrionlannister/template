import { useCallback } from "react";

import { ApiError } from "../types/api-error";
import { API_URL } from "../const/api-url";
import { extractMessage } from "../utils/extract-message";

export const useApiClient = () => {
  const apiClient = useCallback(
    // El default `any` es deliberado para no obligar `<T>` explícito en cada llamada.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async <T = any>(endpoint: string, options: RequestInit = {}): Promise<T> => {
      if (!endpoint.startsWith("/")) throw new Error("endpoint debe empezar con '/'");

      const url = `${API_URL}${endpoint}`;
      const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
      const headers = {
        ...(options.body && !isFormData ? { "Content-Type": "application/json" } : {}),
        ...(options.headers as Record<string, string>),
      };

      const response = await fetch(url, { credentials: "include", ...options, headers });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new ApiError(extractMessage(body, `Error ${response.status}`), response.status);
      }

      if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null as T;
      }
      return await response.json();
    },
    [],
  );

  return { apiClient };
};
