import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate, useParams } from "react-router";
import { Check, Copy, Pencil, RefreshCw, Snowflake, Trash2 } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Modal } from "../../ui/components/modal";
import { Pill } from "../../ui/components/pill";
import { SegmentedControl } from "../../ui/components/segmented-control";
import { Spinner } from "../../ui/components/spinner";
import { StatCard } from "../../ui/components/stat-card";
import { ConstructorFiltro } from "../components/constructor-filtro";
import { etiquetaDeCampo, OPERADOR_LABEL } from "../const/operadores";
import { useAudiences } from "../hooks/use-audiences";
import type { Audiencia, TipoAudiencia } from "../types/audiencia";
import type { CampoFiltro, Condicion } from "../types/filtro";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };
const formatFecha = (iso: string): string => new Date(iso).toLocaleString("es-CO");

export const AudienciaDetallePage: FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { obtenerAudiencia, actualizarAudiencia, duplicarAudiencia, eliminarAudiencia, camposDisponibles } =
    useAudiences();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [audiencia, setAudiencia] = useState<Audiencia | null>(null);
  const [campos, setCampos] = useState<CampoFiltro[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editando, setEditando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [condiciones, setCondiciones] = useState<Condicion[]>([]);
  const [guardando, setGuardando] = useState(false);

  const [duplicarAbierto, setDuplicarAbierto] = useState(false);
  const [tipoDuplicado, setTipoDuplicado] = useState<TipoAudiencia>("dinamica");
  const [duplicando, setDuplicando] = useState(false);

  const [eliminarAbierto, setEliminarAbierto] = useState(false);
  const [eliminando, setEliminando] = useState(false);

  const cargar = useCallback(() => {
    if (!publicId) return Promise.resolve();
    setCargando(true);
    return obtenerAudiencia(publicId)
      .then((resultado) => {
        setAudiencia(resultado);
        setNombre(resultado.nombre);
        setCondiciones(resultado.filtro.and);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la audiencia."))
      .finally(() => setCargando(false));
  }, [publicId, obtenerAudiencia]);

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
    cargar();
  }, [cargar]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  const guardarEdicion = async () => {
    if (!publicId) return;
    setGuardando(true);
    setError(null);
    try {
      const cambios: { nombre?: string; filtro?: { and: Condicion[] } } = { nombre: nombre.trim() };
      if (audiencia?.tipo === "dinamica") cambios.filtro = { and: condiciones };
      const actualizada = await actualizarAudiencia(publicId, cambios);
      setAudiencia(actualizada);
      setEditando(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar los cambios.");
    } finally {
      setGuardando(false);
    }
  };

  const confirmarDuplicado = async () => {
    if (!publicId) return;
    setDuplicando(true);
    try {
      const copia = await duplicarAudiencia(publicId, tipoDuplicado);
      navigate(`/audiencias/${copia.publicId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo duplicar la audiencia.");
      setDuplicarAbierto(false);
    } finally {
      setDuplicando(false);
    }
  };

  const confirmarEliminar = async () => {
    if (!publicId) return;
    setEliminando(true);
    try {
      await eliminarAudiencia(publicId);
      navigate("/audiencias");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo eliminar la audiencia.");
      setEliminando(false);
      setEliminarAbierto(false);
    }
  };

  return (
    <AppShell
      activeHref="/audiencias"
      pageTitle={audiencia?.nombre ?? "Audiencia"}
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre={plan?.nombre ?? ""}
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
    >
      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {cargando || !audiencia ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap mb-1">
                <h1 className="text-[22px]">{audiencia.nombre}</h1>
                {audiencia.tipo === "dinamica" ? (
                  <Pill variant="brand">
                    <RefreshCw className="size-3" aria-hidden />
                    Dinámica
                  </Pill>
                ) : (
                  <Pill variant="neutral">
                    <Snowflake className="size-3" aria-hidden />
                    Estática
                  </Pill>
                )}
              </div>
              <p className="text-ink-2 text-sm">
                {audiencia.tipo === "dinamica"
                  ? "Se evalúa en el momento de cada envío."
                  : `Snapshot congelado el ${audiencia.congeladaEn ? formatFecha(audiencia.congeladaEn) : "—"}.`}
              </p>
            </div>
            <div className="flex gap-2.5 flex-wrap">
              <Button variant="ghost" onClick={() => setDuplicarAbierto(true)}>
                <Copy className="size-4" aria-hidden />
                Duplicar
              </Button>
              {!editando && (
                <Button variant="ghost" onClick={() => setEditando(true)}>
                  <Pencil className="size-4" aria-hidden />
                  Editar
                </Button>
              )}
              <Button variant="ghost" onClick={() => setEliminarAbierto(true)}>
                <Trash2 className="size-4" aria-hidden />
                Eliminar
              </Button>
            </div>
          </div>

          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4 mb-5">
            <StatCard
              label={audiencia.tipo === "dinamica" ? "Contactos ahora" : "Contactos congelados"}
              value={audiencia.conteo.toLocaleString("es-CO")}
            />
          </div>

          {editando ? (
            <div className="bg-surface border border-border rounded-md p-4.25">
              <Field label="Nombre de la audiencia" htmlFor="aud-nombre-editar">
                <Input id="aud-nombre-editar" value={nombre} onChange={(event) => setNombre(event.target.value)} />
              </Field>
              {audiencia.tipo === "dinamica" ? (
                <>
                  <h3 className="text-[16px] font-semibold mb-1">Filtro</h3>
                  <ConstructorFiltro campos={campos} condiciones={condiciones} onChange={setCondiciones} />
                </>
              ) : (
                <p className="text-ink-3 text-xs">
                  El filtro de una audiencia estática no se puede editar; su snapshot ya está congelado.
                </p>
              )}
              <div className="flex gap-2.5 mt-4">
                <Button onClick={guardarEdicion} loading={guardando} disabled={nombre.trim() === ""}>
                  <Check className="size-4" aria-hidden />
                  Guardar cambios
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setEditando(false);
                    setNombre(audiencia.nombre);
                    setCondiciones(audiencia.filtro.and);
                  }}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-md p-4.25">
              <h3 className="text-[16px] font-semibold mb-2.5">Filtro guardado</h3>
              <div className="flex flex-col gap-1.5">
                {audiencia.filtro.and.map((condicion, indice) => (
                  <p key={indice} className="font-mono text-xs bg-surface-2 border border-border rounded-md px-3 py-2">
                    {etiquetaDeCampo(condicion.field)} {OPERADOR_LABEL[condicion.op]}{" "}
                    {condicion.value !== undefined && condicion.value !== null ? `"${condicion.value}"` : ""}
                  </p>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <Modal
        open={duplicarAbierto}
        onClose={() => setDuplicarAbierto(false)}
        title="Duplicar audiencia"
        description="Crea una audiencia nueva con el mismo filtro."
      >
        <div className="mt-2">
          <label className="block text-[13.5px] font-semibold mb-1.75">Tipo de la copia</label>
          <SegmentedControl
            value={tipoDuplicado}
            onChange={(valor) => setTipoDuplicado(valor as TipoAudiencia)}
            options={[
              { value: "dinamica", label: "Dinámica" },
              { value: "estatica", label: "Estática" },
            ]}
          />
          <Button className="w-full justify-center mt-4" onClick={confirmarDuplicado} loading={duplicando}>
            Duplicar
          </Button>
        </div>
      </Modal>

      <Modal
        open={eliminarAbierto}
        onClose={() => setEliminarAbierto(false)}
        title="Eliminar audiencia"
        description={`¿Eliminar "${audiencia?.nombre}"? Esta acción no se puede deshacer.`}
        iconVariant="danger"
      >
        <div className="flex gap-2.5 mt-4">
          <Button variant="danger" onClick={confirmarEliminar} loading={eliminando}>
            <Trash2 className="size-4" aria-hidden />
            Eliminar
          </Button>
          <Button variant="ghost" onClick={() => setEliminarAbierto(false)}>
            Cancelar
          </Button>
        </div>
      </Modal>
    </AppShell>
  );
};
