import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate, useParams } from "react-router";
import { AlertTriangle, Check, Pencil, Play, Trash2, Users } from "lucide-react";
import { useAudiences } from "../../audiences/hooks/use-audiences";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { useContacts } from "../../contacts/hooks/use-contacts";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Modal } from "../../ui/components/modal";
import { Pill } from "../../ui/components/pill";
import { Select } from "../../ui/components/select";
import { Spinner } from "../../ui/components/spinner";
import { Textarea } from "../../ui/components/textarea";
import { CANAL_LABEL, CATEGORIA_LABEL } from "../const/canales";
import { useTemplates } from "../hooks/use-templates";
import type { Plantilla, VerificarAudienciaResultado } from "../types/plantilla";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

export const PlantillaDetallePage: FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { obtenerPlantilla, actualizarPlantilla, eliminarPlantilla, renderizarPlantilla, verificarAudiencia } =
    useTemplates();
  const { listarContactos } = useContacts();
  const { listarAudiencias } = useAudiences();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [plantilla, setPlantilla] = useState<Plantilla | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editando, setEditando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [contenido, setContenido] = useState("");
  const [guardando, setGuardando] = useState(false);

  const [eliminarAbierto, setEliminarAbierto] = useState(false);
  const [eliminando, setEliminando] = useState(false);

  const [busquedaTelefono, setBusquedaTelefono] = useState("");
  const [contactosEncontrados, setContactosEncontrados] = useState<
    { publicId: string; telefono: string }[]
  >([]);
  const [renderizado, setRenderizado] = useState<string | null>(null);
  const [errorRenderizado, setErrorRenderizado] = useState<string | null>(null);
  const [renderizando, setRenderizando] = useState(false);

  const [audiencias, setAudiencias] = useState<{ publicId: string; nombre: string }[]>([]);
  const [audienciaElegida, setAudienciaElegida] = useState("");
  const [resultadoVerificacion, setResultadoVerificacion] = useState<VerificarAudienciaResultado | null>(null);
  const [verificando, setVerificando] = useState(false);

  const cargar = useCallback(() => {
    if (!publicId) return Promise.resolve();
    setCargando(true);
    return obtenerPlantilla(publicId)
      .then((resultado) => {
        setPlantilla(resultado);
        setNombre(resultado.nombre);
        setContenido(resultado.contenido);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la plantilla."))
      .finally(() => setCargando(false));
  }, [publicId, obtenerPlantilla]);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch(() => setUsuario(null));
    listarAudiencias(1, 100)
      .then((resultado) => setAudiencias(resultado.audiencias.map((a) => ({ publicId: a.publicId, nombre: a.nombre }))))
      .catch(() => setAudiencias([]));
  }, [obtenerSesionActual, obtenerMiPlan, listarAudiencias]);

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
      const actualizada = await actualizarPlantilla(publicId, { nombre: nombre.trim(), contenido });
      setPlantilla(actualizada);
      setEditando(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar los cambios.");
    } finally {
      setGuardando(false);
    }
  };

  const confirmarEliminar = async () => {
    if (!publicId) return;
    setEliminando(true);
    try {
      await eliminarPlantilla(publicId);
      navigate("/plantillas");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo eliminar la plantilla.");
      setEliminando(false);
      setEliminarAbierto(false);
    }
  };

  const buscarContactos = async () => {
    if (!busquedaTelefono.trim()) return;
    try {
      const resultado = await listarContactos(1, 5, busquedaTelefono.trim());
      setContactosEncontrados(resultado.contactos.map((c) => ({ publicId: c.publicId, telefono: c.telefono })));
    } catch {
      setContactosEncontrados([]);
    }
  };

  const probarRenderizado = async (contactoPublicId: string) => {
    if (!publicId) return;
    setRenderizando(true);
    setRenderizado(null);
    setErrorRenderizado(null);
    try {
      const texto = await renderizarPlantilla(publicId, contactoPublicId);
      setRenderizado(texto);
    } catch (err) {
      setErrorRenderizado(err instanceof ApiError ? err.message : "No se pudo renderizar la plantilla.");
    } finally {
      setRenderizando(false);
    }
  };

  const ejecutarVerificacion = async () => {
    if (!publicId || !audienciaElegida) return;
    setVerificando(true);
    setResultadoVerificacion(null);
    try {
      const resultado = await verificarAudiencia(publicId, audienciaElegida);
      setResultadoVerificacion(resultado);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo verificar la audiencia.");
    } finally {
      setVerificando(false);
    }
  };

  return (
    <AppShell
      activeHref="/plantillas"
      pageTitle={plantilla?.nombre ?? "Plantilla"}
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

      {cargando || !plantilla ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap mb-1">
                <h1 className="text-[22px]">{plantilla.nombre}</h1>
                <Pill variant={plantilla.canal === "whatsapp" ? "wa" : plantilla.canal === "sms" ? "sms" : "rcs"}>
                  {CANAL_LABEL[plantilla.canal]}
                </Pill>
                {plantilla.categoria && <Pill variant="neutral">{CATEGORIA_LABEL[plantilla.categoria]}</Pill>}
              </div>
              <p className="text-ink-2 text-sm">El canal no se puede cambiar después de creada.</p>
            </div>
            <div className="flex gap-2.5 flex-wrap">
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

          {editando ? (
            <div className="bg-surface border border-border rounded-md p-4.25 mb-4.5 max-w-2xl">
              <Field label="Nombre" htmlFor="tpl-nombre-editar">
                <Input id="tpl-nombre-editar" value={nombre} onChange={(event) => setNombre(event.target.value)} />
              </Field>
              <Field label="Cuerpo del mensaje" htmlFor="tpl-contenido-editar">
                <Textarea
                  id="tpl-contenido-editar"
                  rows={5}
                  value={contenido}
                  onChange={(event) => setContenido(event.target.value)}
                />
              </Field>
              <div className="flex gap-2.5 mt-4">
                <Button onClick={guardarEdicion} loading={guardando} disabled={nombre.trim() === "" || contenido.trim() === ""}>
                  <Check className="size-4" aria-hidden />
                  Guardar cambios
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setEditando(false);
                    setNombre(plantilla.nombre);
                    setContenido(plantilla.contenido);
                  }}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-md p-4.25 mb-4.5 max-w-2xl">
              <h3 className="text-[16px] font-semibold mb-2.5">Cuerpo del mensaje</h3>
              <p className="font-mono text-[13.5px] bg-surface-2 border border-border rounded-md p-3 whitespace-pre-wrap">
                {plantilla.contenido}
              </p>
              {plantilla.variables.length > 0 && (
                <p className="text-ink-3 text-xs mt-2.5">Variables: {plantilla.variables.join(", ")}</p>
              )}
              {plantilla.nombrePlantillaMeta && (
                <p className="text-ink-3 text-xs mt-1">
                  Plantilla aprobada en Meta: <span className="font-mono">{plantilla.nombrePlantillaMeta}</span>
                </p>
              )}
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="bg-surface border border-border rounded-md p-4.25">
              <h3 className="text-[16px] font-semibold mb-1 flex items-center gap-2">
                <Play className="size-4" aria-hidden />
                Renderizado de prueba
              </h3>
              <p className="text-ink-2 text-xs mb-3.5">Busca un contacto real para previsualizar el mensaje.</p>
              <div className="flex gap-2 mb-3">
                <Input
                  value={busquedaTelefono}
                  onChange={(event) => setBusquedaTelefono(event.target.value)}
                  placeholder="Buscar por teléfono…"
                  onKeyDown={(event) => event.key === "Enter" && buscarContactos()}
                />
                <Button variant="secondary" size="sm" onClick={buscarContactos}>
                  Buscar
                </Button>
              </div>
              {contactosEncontrados.length > 0 && (
                <div className="flex flex-col gap-1.5 mb-3.5">
                  {contactosEncontrados.map((contacto) => (
                    <button
                      key={contacto.publicId}
                      type="button"
                      onClick={() => probarRenderizado(contacto.publicId)}
                      className="text-left text-sm border border-border rounded-md px-3 py-2 hover:border-border-strong transition-colors duration-fast ease-out"
                    >
                      {contacto.telefono}
                    </button>
                  ))}
                </div>
              )}
              {renderizando && <Spinner size="sm" />}
              {renderizado && (
                <div className="bg-surface-2 border border-border rounded-md p-3 text-sm whitespace-pre-wrap">
                  {renderizado}
                </div>
              )}
              {errorRenderizado && (
                <p className="text-err-ink text-xs flex items-start gap-1.5 mt-1">
                  <AlertTriangle className="size-3.5 flex-none mt-0.5" aria-hidden />
                  {errorRenderizado}
                </p>
              )}
            </div>

            <div className="bg-surface border border-border rounded-md p-4.25">
              <h3 className="text-[16px] font-semibold mb-1 flex items-center gap-2">
                <Users className="size-4" aria-hidden />
                Verificar variables en una audiencia
              </h3>
              <p className="text-ink-2 text-xs mb-3.5">Avisa qué contactos de una audiencia no tendrían alguna variable.</p>
              <div className="flex gap-2 mb-3.5">
                <Select
                  aria-label="Audiencia"
                  value={audienciaElegida}
                  onChange={(event) => setAudienciaElegida(event.target.value)}
                  options={[{ value: "", label: "Elige una audiencia" }, ...audiencias.map((a) => ({ value: a.publicId, label: a.nombre }))]}
                />
                <Button variant="secondary" size="sm" onClick={ejecutarVerificacion} disabled={!audienciaElegida} loading={verificando}>
                  Verificar
                </Button>
              </div>
              {resultadoVerificacion && (
                <div className="text-sm">
                  <p className="text-ink-2 mb-2">
                    {resultadoVerificacion.contactosConVariableFaltante.length} de {resultadoVerificacion.totalContactos}{" "}
                    contactos no tendrían alguna variable.
                  </p>
                  {resultadoVerificacion.contactosConVariableFaltante.length > 0 && (
                    <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
                      {resultadoVerificacion.contactosConVariableFaltante.map((c) => (
                        <div key={c.contactoPublicId} className="border border-border rounded-md px-3 py-2 text-xs">
                          <span className="font-semibold">{c.telefono}</span> — falta:{" "}
                          {c.variablesFaltantes.join(", ")}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <Modal
        open={eliminarAbierto}
        onClose={() => setEliminarAbierto(false)}
        title="Eliminar plantilla"
        description={`¿Eliminar "${plantilla?.nombre}"? Esta acción no se puede deshacer.`}
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
