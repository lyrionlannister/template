import { useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { Check, RefreshCw, Snowflake } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { SegmentedControl } from "../../ui/components/segmented-control";
import { Spinner } from "../../ui/components/spinner";
import { ConstructorFiltro } from "../components/constructor-filtro";
import { useAudiences } from "../hooks/use-audiences";
import type { TipoAudiencia } from "../types/audiencia";
import type { CampoFiltro, Condicion } from "../types/filtro";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

const filtroValido = (condiciones: Condicion[]): boolean =>
  condiciones.length > 0 &&
  condiciones.every((c) => c.op === "exists" || c.op === "not_exists" || String(c.value ?? "").trim() !== "");

export const NuevaAudienciaPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { camposDisponibles, vistaPrevia, crearAudiencia } = useAudiences();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [campos, setCampos] = useState<CampoFiltro[]>([]);

  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState<TipoAudiencia>("dinamica");
  const [condiciones, setCondiciones] = useState<Condicion[]>([]);
  const [conteo, setConteo] = useState<number | null>(null);
  const [cargandoPreview, setCargandoPreview] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch(() => setUsuario(null));
    camposDisponibles()
      .then((lista) => setCampos(lista))
      .catch(() => setCampos([]));
  }, [obtenerSesionActual, obtenerMiPlan, camposDisponibles]);

  useEffect(() => {
    if (!filtroValido(condiciones)) {
      setConteo(null);
      return;
    }
    let vigente = true;
    setCargandoPreview(true);
    const temporizador = setTimeout(() => {
      vistaPrevia({ and: condiciones })
        .then((valor) => vigente && setConteo(valor))
        .catch(() => vigente && setConteo(null))
        .finally(() => vigente && setCargandoPreview(false));
    }, 400);
    return () => {
      vigente = false;
      clearTimeout(temporizador);
    };
  }, [condiciones, vistaPrevia]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  const guardar = async () => {
    setError(null);
    setGuardando(true);
    try {
      const audiencia = await crearAudiencia(nombre.trim(), tipo, { and: condiciones });
      navigate(`/audiencias/${audiencia.publicId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar la audiencia.");
    } finally {
      setGuardando(false);
    }
  };

  const puedeGuardar = nombre.trim() !== "" && filtroValido(condiciones) && !guardando;

  return (
    <AppShell
      activeHref="/audiencias"
      pageTitle="Nueva audiencia"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre={plan?.nombre ?? ""}
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Nueva audiencia</h1>
        <p className="text-ink-2 text-sm">Define el filtro sobre las variables de tus contactos.</p>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.65fr_1fr] items-start">
        <div className="flex flex-col gap-4">
          <div className="bg-surface border border-border rounded-md p-4.25">
            <Field label="Nombre de la audiencia" htmlFor="aud-nombre">
              <Input
                id="aud-nombre"
                value={nombre}
                onChange={(event) => setNombre(event.target.value)}
                placeholder="Ej. Clientes CDMX con saldo"
              />
            </Field>
            <label className="block text-[13.5px] font-semibold mb-1.75">Tipo de audiencia</label>
            <SegmentedControl
              value={tipo}
              onChange={(valor) => setTipo(valor as TipoAudiencia)}
              options={[
                { value: "dinamica", label: "Dinámica" },
                { value: "estatica", label: "Estática" },
              ]}
            />
            <p className="text-ink-2 text-xs mt-2.5 flex items-start gap-1.5">
              {tipo === "dinamica" ? (
                <>
                  <RefreshCw className="size-3.5 flex-none mt-0.5" aria-hidden />
                  El filtro se evalúa en cada envío. Quien entre o salga de la condición, entra o sale solo.
                </>
              ) : (
                <>
                  <Snowflake className="size-3.5 flex-none mt-0.5" aria-hidden />
                  El filtro se evalúa una sola vez, al crearla. La lista queda congelada para siempre.
                </>
              )}
            </p>
          </div>

          <div className="bg-surface border border-border rounded-md p-4.25">
            <h3 className="text-[16px] font-semibold mb-1">Filtro</h3>
            <ConstructorFiltro campos={campos} condiciones={condiciones} onChange={setCondiciones} />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-md p-4.25">
          <h3 className="text-[16px] font-semibold mb-1">Vista previa</h3>
          <p className="text-ink-2 text-xs mb-3.5">Conteo {tipo === "dinamica" ? "en vivo" : "al congelar"}.</p>
          <div className="flex items-baseline gap-2.5 mb-4">
            {cargandoPreview ? (
              <Spinner size="sm" />
            ) : (
              <span className="font-display text-[38px] font-bold leading-none">{conteo ?? "—"}</span>
            )}
          </div>
          <Button className="w-full justify-center" onClick={guardar} disabled={!puedeGuardar} loading={guardando}>
            <Check className="size-4" aria-hidden />
            Guardar audiencia {tipo === "dinamica" ? "dinámica" : "y congelar snapshot"}
          </Button>
          <p className="text-ink-3 text-xs text-center mt-2">
            {tipo === "dinamica" ? "Solo se guarda el filtro, no la lista." : "Se congela la lista de contactos que cumplen hoy."}
          </p>
        </div>
      </div>
    </AppShell>
  );
};
