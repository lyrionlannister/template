import { useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { Settings, Users } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { cn } from "../../shared/utils/cn";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { SelectableCardGroup } from "../../ui/components/selectable-card-group";
import { Spinner } from "../../ui/components/spinner";
import { useContacts } from "../hooks/use-contacts";
import type { PoliticaConflictoVariables } from "../types/configuracion";

const NAV_ITEMS = [
  { label: "Contactos", href: "/contactos", icon: Users },
  { label: "Ajustes", href: "/ajustes", icon: Settings },
];

const OPCIONES_POLITICA: { value: PoliticaConflictoVariables; label: string; description: string }[] = [
  {
    value: "ultimo_gana",
    label: "El valor más reciente gana",
    description: "La reimportación reemplaza el valor anterior.",
  },
  {
    value: "no_pisar_marcar_advertencia",
    label: "No sobrescribir",
    description: "Se conserva el valor anterior y la fila queda marcada con advertencia.",
  },
];

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

export const ConfiguracionContactosPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual } = useAuth();
  const { obtenerConfiguracion, actualizarConfiguracion } = useContacts();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [politica, setPolitica] = useState<PoliticaConflictoVariables | null>(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guardadoOk, setGuardadoOk] = useState(false);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerConfiguracion()])
      .then(([sesion, configuracion]) => {
        setUsuario(sesion);
        setPolitica(configuracion.politicaConflictoVariables);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la configuración."))
      .finally(() => setCargando(false));
  }, [obtenerSesionActual, obtenerConfiguracion]);

  const esAdministrador = usuario?.rol === "administrador";

  const cambiarPolitica = async (nuevaPolitica: PoliticaConflictoVariables) => {
    setGuardando(true);
    setError(null);
    setGuardadoOk(false);
    try {
      const configuracion = await actualizarConfiguracion(nuevaPolitica);
      setPolitica(configuracion.politicaConflictoVariables);
      setGuardadoOk(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar la configuración.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      navItems={NAV_ITEMS}
      activeHref="/contactos"
      logoLabel="Pulso"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
        <div>
          <h1 className="text-[22px] mb-1">Configuración de contactos</h1>
          <p className="text-ink-2 text-sm">Qué hacer cuando una reimportación trae un valor distinto.</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => navigate("/contactos")}>
          Volver al listado
        </Button>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
          <div className="flex items-center gap-2.5 mb-1">
            <h3 className="text-[15px] font-semibold">Política de conflicto de variables</h3>
            {guardando && <Spinner />}
          </div>
          <p className="text-ink-2 text-sm mb-4.5">
            Un conflicto ocurre cuando una importación trae un valor distinto para una variable que el contacto ya
            tenía. Sin importar la política elegida, todo conflicto queda registrado y se puede revertir desde el
            detalle del contacto.
          </p>

          {!esAdministrador && (
            <div className="mb-4.5">
              <Alert variant="info" title="Solo lectura">
                Solo un administrador de la organización puede cambiar esta configuración.
              </Alert>
            </div>
          )}

          {error && (
            <div className="mb-4.5 animate-[toastIn_var(--duration-slow)_var(--ease-spring)]">
              <Alert variant="err" title="No se pudo guardar" onClose={() => setError(null)}>
                {error}
              </Alert>
            </div>
          )}

          {guardadoOk && (
            <div className="mb-4.5 animate-[toastIn_var(--duration-slow)_var(--ease-spring)]">
              <Alert variant="ok" title="Guardado" onClose={() => setGuardadoOk(false)}>
                La política se actualizó correctamente.
              </Alert>
            </div>
          )}

          {politica && (
            <div
              className={cn(
                "transition-opacity duration-fast ease-out",
                guardando && "opacity-60 pointer-events-none",
              )}
            >
              <SelectableCardGroup
                options={OPCIONES_POLITICA}
                value={politica}
                onChange={(valor) => {
                  if (esAdministrador && !guardando) cambiarPolitica(valor as PoliticaConflictoVariables);
                }}
              />
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
};
