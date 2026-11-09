import { useEffect, useRef, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { Check, MessageCircle, MessageSquareText, MessagesSquare } from "lucide-react";
import { useAudiences } from "../../audiences/hooks/use-audiences";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Plan } from "../../auth/types/plan";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Select } from "../../ui/components/select";
import { Textarea } from "../../ui/components/textarea";
import { CANAL_LABEL, CANALES, CATEGORIA_LABEL } from "../const/canales";
import { useTemplates } from "../hooks/use-templates";
import type { CanalMensajeria, CategoriaMensaje } from "../types/plantilla";
import { extraerVariables } from "../utils/extraer-variables";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

const CANAL_ICONO: Record<CanalMensajeria, FC<{ className?: string }>> = {
  whatsapp: MessageCircle,
  sms: MessageSquareText,
  rcs: MessagesSquare,
};

const CATEGORIAS_PLANTILLA: CategoriaMensaje[] = ["marketing", "utility"];

export const NuevaPlantillaPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, obtenerMiPlan, cerrarSesion } = useAuth();
  const { crearPlantilla } = useTemplates();
  const { camposDisponibles } = useAudiences();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [clavesSugeridas, setClavesSugeridas] = useState<string[]>([]);

  const [nombre, setNombre] = useState("");
  const [canal, setCanal] = useState<CanalMensajeria>("sms");
  const [contenido, setContenido] = useState("");
  const [categoria, setCategoria] = useState<CategoriaMensaje>("utility");
  const [nombrePlantillaMeta, setNombrePlantillaMeta] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch(() => setUsuario(null));
    camposDisponibles()
      .then((campos) =>
        setClavesSugeridas(
          campos.filter((c) => c.field.startsWith("variables.")).map((c) => c.field.slice("variables.".length)),
        ),
      )
      .catch(() => setClavesSugeridas([]));
  }, [obtenerSesionActual, obtenerMiPlan, camposDisponibles]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  const insertarVariable = (clave: string) => {
    const textarea = textareaRef.current;
    const placeholder = `{{${clave}}}`;
    if (!textarea) {
      setContenido((actual) => actual + placeholder);
      return;
    }
    const inicio = textarea.selectionStart ?? contenido.length;
    const fin = textarea.selectionEnd ?? contenido.length;
    setContenido(contenido.slice(0, inicio) + placeholder + contenido.slice(fin));
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.setSelectionRange(inicio + placeholder.length, inicio + placeholder.length);
    });
  };

  const variables = extraerVariables(contenido);
  const esWhatsapp = canal === "whatsapp";
  const puedeGuardar =
    nombre.trim() !== "" && contenido.trim() !== "" && (!esWhatsapp || nombrePlantillaMeta.trim() !== "") && !guardando;

  const guardar = async () => {
    setError(null);
    setGuardando(true);
    try {
      const plantilla = await crearPlantilla({
        nombre: nombre.trim(),
        canal,
        contenido,
        categoria: esWhatsapp ? categoria : null,
        nombrePlantillaMeta: esWhatsapp ? nombrePlantillaMeta.trim() : null,
      });
      navigate(`/plantillas/${plantilla.publicId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar la plantilla.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      activeHref="/plantillas"
      pageTitle="Nueva plantilla"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre={plan?.nombre ?? ""}
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Nueva plantilla</h1>
        <p className="text-ink-2 text-sm">Escribe el mensaje una vez y personalízalo con las variables de cada contacto.</p>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="bg-surface border border-border rounded-md p-4.25 max-w-2xl">
        <label className="block text-[13.5px] font-semibold mb-1.75">Canal</label>
        <div className="grid grid-cols-3 gap-2 mb-4.5">
          {CANALES.map((opcion) => {
            const Icono = CANAL_ICONO[opcion];
            return (
              <button
                key={opcion}
                type="button"
                onClick={() => setCanal(opcion)}
                className={`flex flex-col items-center gap-1.5 rounded-[13px] border px-3 py-3 text-[13.5px] font-semibold transition-colors duration-fast ease-out ${
                  canal === opcion ? "border-brand bg-brand-soft text-brand-ink" : "border-border text-ink-2 hover:border-border-strong"
                }`}
              >
                <Icono className="size-5" />
                {CANAL_LABEL[opcion]}
              </button>
            );
          })}
        </div>

        <Field label="Nombre" htmlFor="tpl-nombre">
          <Input id="tpl-nombre" value={nombre} onChange={(event) => setNombre(event.target.value)} placeholder="Ej. recordatorio_pago" />
        </Field>

        {esWhatsapp && (
          <div className="grid gap-4.5 sm:grid-cols-2 mb-4.5">
            <Field label="Categoría" htmlFor="tpl-categoria">
              <Select
                id="tpl-categoria"
                value={categoria}
                onChange={(event) => setCategoria(event.target.value as CategoriaMensaje)}
                options={CATEGORIAS_PLANTILLA.map((c) => ({ value: c, label: CATEGORIA_LABEL[c] }))}
              />
            </Field>
            <Field label="Nombre de la plantilla en Meta" htmlFor="tpl-meta" hint="Referencia a la plantilla aprobada en la cuenta de WhatsApp Business del cliente.">
              <Input id="tpl-meta" value={nombrePlantillaMeta} onChange={(event) => setNombrePlantillaMeta(event.target.value)} />
            </Field>
          </div>
        )}

        <Field label="Cuerpo del mensaje" htmlFor="tpl-contenido">
          <Textarea
            id="tpl-contenido"
            ref={textareaRef}
            rows={5}
            value={contenido}
            onChange={(event) => setContenido(event.target.value)}
            placeholder="Hola {{nombre}}, tu saldo es {{saldo}}."
          />
        </Field>

        {clavesSugeridas.length > 0 && (
          <div className="flex flex-wrap gap-1.5 -mt-2.5 mb-4.5">
            <span className="text-xs text-ink-3 self-center">Insertar variable:</span>
            {clavesSugeridas.map((clave) => (
              <button
                key={clave}
                type="button"
                onClick={() => insertarVariable(clave)}
                className="text-xs font-mono bg-surface-2 border border-border rounded-full px-2.5 py-1 hover:border-border-strong transition-colors duration-fast ease-out"
              >
                {`{{${clave}}}`}
              </button>
            ))}
          </div>
        )}

        {variables.length > 0 && (
          <p className="text-ink-3 text-xs mb-4.5">Variables detectadas: {variables.join(", ")}</p>
        )}

        <Button className="w-full justify-center" onClick={guardar} disabled={!puedeGuardar} loading={guardando}>
          <Check className="size-4" aria-hidden />
          Crear plantilla
        </Button>
      </div>
    </AppShell>
  );
};
