import { useCallback } from "react";
import { GOOGLE_CLIENT_ID } from "../const/google-config";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (respuesta: { credential: string }) => void }) => void;
          prompt: (callback?: (notificacion: { isNotDisplayed: () => boolean; isSkippedMoment: () => boolean }) => void) => void;
        };
      };
    };
  }
}

const SCRIPT_SRC = "https://accounts.google.com/gsi/client";
let scriptPromise: Promise<void> | null = null;

const cargarScript = (): Promise<void> => {
  if (window.google?.accounts.id) return Promise.resolve();
  if (scriptPromise) return scriptPromise;
  scriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("No se pudo cargar el inicio de sesión de Google."));
    document.head.appendChild(script);
  });
  return scriptPromise;
};

export const useGoogleIdentity = () => {
  const iniciarSesionConGoogle = useCallback(
    () =>
      cargarScript().then(
        () =>
          new Promise<string>((resolve, reject) => {
            window.google!.accounts.id.initialize({
              client_id: GOOGLE_CLIENT_ID,
              callback: (respuesta) => resolve(respuesta.credential),
            });
            window.google!.accounts.id.prompt((notificacion) => {
              if (notificacion.isNotDisplayed() || notificacion.isSkippedMoment()) {
                reject(new Error("No se pudo mostrar el inicio de sesión de Google."));
              }
            });
          }),
      ),
    [],
  );

  return { iniciarSesionConGoogle };
};
