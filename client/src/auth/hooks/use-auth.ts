import { useCallback } from "react";
import { useApiClient } from "../../shared/hooks/use-api-client";
import type { CanalOtp } from "../types/canal-otp";
import type { Plan } from "../types/plan";
import type { Usuario } from "../types/usuario";

export const useAuth = () => {
  const { apiClient } = useApiClient();

  const registrar = useCallback(
    (datos: { nombreOrganizacion: string; email: string; password: string }) =>
      apiClient<Usuario>("/auth/registro", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const login = useCallback(
    (datos: { email: string; password: string }) =>
      apiClient<Usuario>("/auth/login", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  const loginConGoogle = useCallback(
    (idToken: string) =>
      apiClient<Usuario>("/auth/google", { method: "POST", body: JSON.stringify({ idToken }) }),
    [apiClient],
  );

  const solicitarRecuperacion = useCallback(
    (email: string) =>
      apiClient<null>("/auth/password/olvide", { method: "POST", body: JSON.stringify({ email }) }),
    [apiClient],
  );

  const restablecerPassword = useCallback(
    (token: string, nuevaPassword: string) =>
      apiClient<null>("/auth/password/restablecer", {
        method: "POST",
        body: JSON.stringify({ token, nuevaPassword }),
      }),
    [apiClient],
  );

  const enviarOtp = useCallback(
    (canal: CanalOtp) => apiClient<null>("/auth/otp/enviar", { method: "POST", body: JSON.stringify({ canal }) }),
    [apiClient],
  );

  const verificarOtp = useCallback(
    (codigo: string, canal: CanalOtp) =>
      apiClient<null>("/auth/otp/verificar", { method: "POST", body: JSON.stringify({ codigo, canal }) }),
    [apiClient],
  );

  const cerrarSesion = useCallback(() => apiClient<unknown>("/auth/logout", { method: "POST" }), [apiClient]);

  const obtenerSesionActual = useCallback(() => apiClient<Usuario>("/auth/yo"), [apiClient]);

  const obtenerMiPlan = useCallback(() => apiClient<Plan>("/auth/mi-plan"), [apiClient]);

  const invitarUsuario = useCallback(
    (datos: { email: string; password: string }) =>
      apiClient<Usuario>("/auth/usuarios", { method: "POST", body: JSON.stringify(datos) }),
    [apiClient],
  );

  return {
    registrar,
    login,
    loginConGoogle,
    solicitarRecuperacion,
    restablecerPassword,
    enviarOtp,
    verificarOtp,
    cerrarSesion,
    obtenerSesionActual,
    obtenerMiPlan,
    invitarUsuario,
  };
};
