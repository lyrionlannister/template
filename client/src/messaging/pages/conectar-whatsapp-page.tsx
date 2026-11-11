import { useCallback, useEffect, useRef, useState, type FC } from "react";
import { MessageCircle } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Spinner } from "../../ui/components/spinner";
import { META_APP_ID, META_CONFIG_ID } from "../const/meta-config";
import { useMessaging } from "../hooks/use-messaging";
import type { ConexionWhatsapp } from "../types/conexion-whatsapp";
import { cargarFacebookSdk, type FacebookLoginResponse } from "../utils/load-facebook-sdk";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

interface DatosEmbeddedSignup {
  wabaId: string;
  phoneNumberId: string;
}

export const ConectarWhatsappPage: FC = () => {
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { conectarWhatsapp } = useMessaging();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const [conectando, setConectando] = useState(false);
  const [errorConexion, setErrorConexion] = useState<string | null>(null);
  const [conexion, setConexion] = useState<ConexionWhatsapp | null>(null);

  const datosSignupRef = useRef<DatosEmbeddedSignup | null>(null);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch((err) =>
        setErrorCarga(err instanceof Error ? err.message : "No se pudo cargar esta página."),
      )
      .finally(() => setCargando(false));
  }, [obtenerSesionActual, obtenerMiPlan]);

  useEffect(() => {
    const alRecibirMensaje = (event: MessageEvent) => {
      if (event.origin !== "https://www.facebook.com") return;
      // El SDK de Meta manda las claves del evento en snake_case
      // (waba_id, phone_number_id), no en el camelCase del resto del front.
      let payload: {
        type?: string;
        event?: string;
        data?: { waba_id?: string; phone_number_id?: string };
      };
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }
      if (
        payload.type === "WA_EMBEDDED_SIGNUP" &&
        payload.event === "FINISH" &&
        payload.data?.waba_id &&
        payload.data?.phone_number_id
      ) {
        datosSignupRef.current = {
          wabaId: payload.data.waba_id,
          phoneNumberId: payload.data.phone_number_id,
        };
      }
    };
    window.addEventListener("message", alRecibirMensaje);
    return () => window.removeEventListener("message", alRecibirMensaje);
  }, []);

  const salir = async () => {
    await cerrarSesion();
  };

  const conectar = useCallback(async () => {
    setConectando(true);
    setErrorConexion(null);
    datosSignupRef.current = null;
    try {
      const fb = await cargarFacebookSdk(META_APP_ID);
      const code = await new Promise<string>((resolve, reject) => {
        fb.login(
          (response: FacebookLoginResponse) => {
            if (response.authResponse?.code) resolve(response.authResponse.code);
            else reject(new Error("Conexión cancelada o rechazada por Meta."));
          },
          {
            config_id: META_CONFIG_ID,
            response_type: "code",
            override_default_response_type: true,
            extras: { feature: "whatsapp_embedded_signup", sessionInfoVersion: "3" },
          },
        );
      });

      // El cast evita que TS "recuerde" el `= null` de la línea de arriba:
      // entre medio corrió el login real de Meta, que sí puede haber
      // llenado la ref desde el listener de `message` (otro closure).
      const datosSignup = datosSignupRef.current as DatosEmbeddedSignup | null;
      if (!datosSignup) {
        throw new Error("Meta no envió los datos del número conectado. Intenta de nuevo.");
      }

      const nuevaConexion = await conectarWhatsapp({
        code,
        wabaId: datosSignup.wabaId,
        phoneNumberId: datosSignup.phoneNumberId,
      });
      setConexion(nuevaConexion);
    } catch (err) {
      setErrorConexion(err instanceof Error ? err.message : "No se pudo conectar WhatsApp.");
    } finally {
      setConectando(false);
    }
  }, [conectarWhatsapp]);

  return (
    <AppShell
      activeHref="/whatsapp/conectar"
      pageTitle="WhatsApp"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre={plan?.nombre ?? ""}
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Conectar WhatsApp</h1>
        <p className="text-ink-2 text-sm">
          Vincula el WhatsApp Business de tu organización para enviar mensajes reales.
        </p>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : errorCarga ? (
        <Alert variant="err" title="No se pudo cargar esta página">
          {errorCarga}
        </Alert>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
          <h3 className="text-[15px] font-semibold mb-1 flex items-center gap-2">
            <MessageCircle className="size-4.5 text-brand" aria-hidden />
            Número de WhatsApp
          </h3>

          {conexion ? (
            <Alert variant="ok" title="WhatsApp conectado">
              {conexion.numeroTelefono} quedó conectado a tu organización.
            </Alert>
          ) : (
            <>
              <p className="text-ink-2 text-sm mb-4.5">
                Te llevará a iniciar sesión con Facebook para elegir o crear tu WhatsApp Business.
              </p>
              {errorConexion && (
                <div className="mb-4.5">
                  <Alert variant="err" title="No se pudo conectar">
                    {errorConexion}
                  </Alert>
                </div>
              )}
              <Button onClick={conectar} loading={conectando} className="w-full justify-center">
                Conectar WhatsApp
              </Button>
            </>
          )}
        </div>
      )}
    </AppShell>
  );
};
