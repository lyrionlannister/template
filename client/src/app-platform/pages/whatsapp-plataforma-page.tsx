import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { RefreshCw, ShieldCheck } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Pill } from "../../ui/components/pill";
import { Spinner } from "../../ui/components/spinner";
import { ESTADO_PLANTILLA_LABEL, ESTADO_PLANTILLA_PILL } from "../const/labels";
import { usePlantillaOtpPlataforma } from "../hooks/use-plantilla-otp-plataforma";
import type { PlantillaOtpPlataforma } from "../types/plantilla-otp-plataforma";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

export const WhatsappPlataformaPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, cerrarSesion } = useAuth();
  const { listar, crear, sincronizar } = usePlantillaOtpPlataforma();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plantilla, setPlantilla] = useState<PlantillaOtpPlataforma | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nombre, setNombre] = useState("pulso_otp");
  const [idioma, setIdioma] = useState("es");
  const [creando, setCreando] = useState(false);
  const [sincronizando, setSincronizando] = useState(false);

  const cargar = useCallback(
    () =>
      listar()
        .then((lista) => setPlantilla(lista[0] ?? null))
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la plantilla."))
        .finally(() => setCargando(false)),
    [listar],
  );

  useEffect(() => {
    obtenerSesionActual()
      .then(setUsuario)
      .catch(() => setUsuario(null));
  }, [obtenerSesionActual]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  const crearPlantilla = async () => {
    setError(null);
    setCreando(true);
    try {
      const nueva = await crear(nombre.trim(), idioma.trim());
      setPlantilla(nueva);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la plantilla en Meta.");
    } finally {
      setCreando(false);
    }
  };

  const sincronizarEstado = async () => {
    if (!plantilla) return;
    setError(null);
    setSincronizando(true);
    try {
      const actualizada = await sincronizar(plantilla.publicId);
      setPlantilla(actualizada);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo consultar el estado en Meta.");
    } finally {
      setSincronizando(false);
    }
  };

  return (
    <AppShell
      activeHref="/app-platform/whatsapp-plataforma"
      pageTitle="WhatsApp de plataforma"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre="Administrador del sistema"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
      esSuperadmin
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">WhatsApp de plataforma</h1>
        <p className="text-ink-2 text-sm">
          Plantilla de autenticación con la que sale el OTP de inicio de sesión. Identidad de Pulso, nunca la de un
          tenant.
        </p>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : !plantilla ? (
        <div className="bg-surface border border-border rounded-md p-4.25 max-w-xl">
          <h3 className="font-semibold text-[15px] mb-3">Crear plantilla de autenticación</h3>
          <div className="grid gap-4.5 sm:grid-cols-2 mb-4.5">
            <Field label="Nombre" htmlFor="otp-nombre">
              <Input id="otp-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
            </Field>
            <Field label="Idioma" htmlFor="otp-idioma" hint="Código de idioma de Meta, ej. es.">
              <Input id="otp-idioma" value={idioma} onChange={(e) => setIdioma(e.target.value)} />
            </Field>
          </div>
          <Button onClick={crearPlantilla} loading={creando} disabled={nombre.trim() === "" || idioma.trim() === ""}>
            Crear en Meta
          </Button>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.25 max-w-xl">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-soft grid place-items-center">
                <ShieldCheck className="size-5 text-brand-ink" aria-hidden />
              </div>
              <div>
                <h3 className="font-semibold text-[15px]">{plantilla.nombre}</h3>
                <p className="text-ink-3 text-xs">Idioma: {plantilla.idioma}</p>
              </div>
            </div>
            <Pill variant={ESTADO_PLANTILLA_PILL[plantilla.estadoMeta]}>
              {ESTADO_PLANTILLA_LABEL[plantilla.estadoMeta]}
            </Pill>
          </div>

          {plantilla.estadoMeta === "APPROVED" ? (
            <p className="text-ink-2 text-sm">
              El OTP de login por WhatsApp ya puede salir con esta plantilla y la identidad de plataforma.
            </p>
          ) : (
            <>
              <p className="text-ink-2 text-sm mb-4">
                Meta aún no aprueba esta plantilla. El OTP por WhatsApp no sale hasta que quede aprobada.
              </p>
              <Button variant="secondary" onClick={sincronizarEstado} loading={sincronizando}>
                <RefreshCw className="size-4" aria-hidden />
                Sincronizar estado
              </Button>
            </>
          )}
        </div>
      )}
    </AppShell>
  );
};
