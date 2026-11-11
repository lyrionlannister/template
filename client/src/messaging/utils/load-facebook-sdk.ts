// Carga perezosa e idempotente del SDK de JavaScript de Meta. No existe
// otra referencia a este SDK en el repo -- se agrega desde cero solo para
// el botón de Embedded Signup de WhatsApp.

export interface FacebookLoginResponse {
  authResponse: { code: string } | null;
  status: string;
}

interface FacebookSdk {
  init: (params: { appId: string; version: string; xfbml?: boolean }) => void;
  login: (
    callback: (response: FacebookLoginResponse) => void,
    params: {
      config_id: string;
      response_type: "code";
      override_default_response_type: true;
      // Sin esto, FB.login hace un login genérico de consentimiento y
      // nunca abre el asistente de Embedded Signup (elegir/crear WABA y
      // número) -- es justo lo que activa ese flujo, no un detalle opcional.
      extras: { feature: "whatsapp_embedded_signup"; sessionInfoVersion: "3" };
    },
  ) => void;
}

declare global {
  interface Window {
    FB?: FacebookSdk;
    fbAsyncInit?: () => void;
  }
}

const SDK_URL = "https://connect.facebook.net/es_LA/sdk.js";
const SDK_VERSION = "v27.0";

let sdkPromesa: Promise<FacebookSdk> | null = null;

export const cargarFacebookSdk = (appId: string): Promise<FacebookSdk> => {
  if (sdkPromesa) return sdkPromesa;

  sdkPromesa = new Promise((resolve) => {
    window.fbAsyncInit = () => {
      window.FB!.init({ appId, version: SDK_VERSION, xfbml: false });
      resolve(window.FB!);
    };

    if (document.getElementById("facebook-jssdk")) return;
    const script = document.createElement("script");
    script.id = "facebook-jssdk";
    script.src = SDK_URL;
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  });

  return sdkPromesa;
};
