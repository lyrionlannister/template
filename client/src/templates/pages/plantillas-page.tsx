import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { LayoutTemplate, Plus } from "lucide-react";
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
import { CANAL_LABEL, CATEGORIA_LABEL } from "../const/canales";
import { useTemplates } from "../hooks/use-templates";
import type { Plantilla } from "../types/plantilla";

const POR_PAGINA = 20;

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

export const PlantillasPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { listarPlantillas } = useTemplates();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(
    () =>
      listarPlantillas(1, POR_PAGINA)
        .then((resultado) => setPlantillas(resultado.plantillas))
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar las plantillas."))
        .finally(() => setCargando(false)),
    [listarPlantillas],
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
      activeHref="/plantillas"
      pageTitle="Plantillas"
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
          <h1 className="text-[22px] mb-1">Plantillas</h1>
          <p className="text-ink-2 text-sm">Mensajes reutilizables por canal, con variables de tus contactos.</p>
        </div>
        <Button onClick={() => navigate("/plantillas/nueva")}>
          <Plus className="size-4" aria-hidden />
          Nueva plantilla
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
      ) : plantillas.length === 0 ? (
        <EmptyState
          icon={LayoutTemplate}
          title="Todavía no hay plantillas"
          description="Crea el mensaje que tus campañas van a reutilizar."
          action={<Button onClick={() => navigate("/plantillas/nueva")}>Nueva plantilla</Button>}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {plantillas.map((plantilla) => (
            <button
              key={plantilla.publicId}
              type="button"
              onClick={() => navigate(`/plantillas/${plantilla.publicId}`)}
              className="bg-surface border border-border rounded-md p-4.25 text-left hover:border-border-strong transition-colors duration-fast ease-out"
            >
              <div className="flex items-start justify-between gap-2.5 mb-2.5">
                <Pill variant={plantilla.canal === "whatsapp" ? "wa" : plantilla.canal === "sms" ? "sms" : "rcs"}>
                  {CANAL_LABEL[plantilla.canal]}
                </Pill>
                {plantilla.categoria && <Pill variant="neutral">{CATEGORIA_LABEL[plantilla.categoria]}</Pill>}
              </div>
              <h3 className="font-semibold text-[15px] mb-2">{plantilla.nombre}</h3>
              <p className="text-ink-2 text-xs line-clamp-3 bg-surface-2 border border-border rounded-md p-2.5">
                {plantilla.contenido}
              </p>
            </button>
          ))}
        </div>
      )}
    </AppShell>
  );
};
