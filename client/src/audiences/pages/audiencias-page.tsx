import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { Filter, Plus, RefreshCw, Snowflake } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { EmptyState } from "../../ui/components/empty-state";
import { Pill } from "../../ui/components/pill";
import { Spinner } from "../../ui/components/spinner";
import { useAudiences } from "../hooks/use-audiences";
import type { Audiencia } from "../types/audiencia";

const POR_PAGINA = 20;

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

const TipoPill: FC<{ tipo: Audiencia["tipo"] }> = ({ tipo }) =>
  tipo === "dinamica" ? (
    <Pill variant="brand">
      <RefreshCw className="size-3" aria-hidden />
      Dinámica
    </Pill>
  ) : (
    <Pill variant="neutral">
      <Snowflake className="size-3" aria-hidden />
      Estática
    </Pill>
  );

export const AudienciasPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { listarAudiencias } = useAudiences();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [audiencias, setAudiencias] = useState<Audiencia[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(
    () =>
      listarAudiencias(1, POR_PAGINA)
        .then((resultado) => setAudiencias(resultado.audiencias))
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar las audiencias."))
        .finally(() => setCargando(false)),
    [listarAudiencias],
  );

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch(() => setUsuario(null));
  }, [obtenerSesionActual, obtenerMiPlan]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  return (
    <AppShell
      activeHref="/audiencias"
      pageTitle="Audiencias"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre={plan?.nombre ?? ""}
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
        <div>
          <h1 className="text-[22px] mb-1">Audiencias</h1>
          <p className="text-ink-2 text-sm">Filtros guardados sobre las variables de tus contactos.</p>
        </div>
        <Button onClick={() => navigate("/audiencias/nueva")}>
          <Plus className="size-4" aria-hidden />
          Nueva audiencia
        </Button>
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
      ) : audiencias.length === 0 ? (
        <EmptyState
          icon={Filter}
          title="Todavía no hay audiencias"
          description="Crea un filtro sobre tus contactos para empezar a segmentar tus envíos."
          action={<Button onClick={() => navigate("/audiencias/nueva")}>Nueva audiencia</Button>}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {audiencias.map((audiencia) => (
            <button
              key={audiencia.publicId}
              type="button"
              onClick={() => navigate(`/audiencias/${audiencia.publicId}`)}
              className="bg-surface border border-border rounded-md p-4.25 text-left hover:border-border-strong transition-colors duration-fast ease-out"
            >
              <div className="flex items-start justify-between gap-2.5 mb-2.5">
                <span className="font-semibold text-[15px]">{audiencia.nombre}</span>
                <TipoPill tipo={audiencia.tipo} />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="font-display text-[22px] font-bold">{audiencia.conteo.toLocaleString("es-CO")}</span>
                <span className="text-ink-3 text-xs">
                  {audiencia.tipo === "dinamica" ? "contactos ahora" : "contactos congelados"}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </AppShell>
  );
};
