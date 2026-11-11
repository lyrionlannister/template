import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate, useParams } from "react-router";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Spinner } from "../../ui/components/spinner";
import { usePlanes } from "../hooks/use-planes";
import type { Plan, PlanRequest } from "../types/plan";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

export const PlanDetallePage: FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const navigate = useNavigate();
  const { obtenerSesionActual, cerrarSesion } = useAuth();
  const { listarPlanes, actualizarPlan } = usePlanes();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [form, setForm] = useState<PlanRequest | null>(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guardado, setGuardado] = useState(false);

  const cargar = useCallback(() => {
    if (!publicId) return Promise.resolve();
    return listarPlanes()
      .then((planes) => {
        const encontrado = planes.find((p) => p.publicId === publicId) ?? null;
        setPlan(encontrado);
        if (encontrado) {
          const { publicId: _ignorado, creadoEn: _creadoEn, ...resto } = encontrado;
          setForm(resto);
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el plan."))
      .finally(() => setCargando(false));
  }, [publicId, listarPlanes]);

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

  const guardar = async () => {
    if (!publicId || !form) return;
    setError(null);
    setGuardando(true);
    setGuardado(false);
    try {
      const actualizado = await actualizarPlan(publicId, form);
      setPlan(actualizado);
      setGuardado(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el plan.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      activeHref="/app-platform/planes"
      pageTitle={plan ? plan.nombre : "Plan"}
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre="Administrador del sistema"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
      esSuperadmin
    >
      <Button variant="ghost" size="sm" onClick={() => navigate("/app-platform/planes")} className="mb-4">
        ← Volver a planes
      </Button>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}
      {guardado && (
        <div className="mb-4.5">
          <Alert variant="ok" title="Plan actualizado">
            El cambio ya rige para los tenants en este plan.
          </Alert>
        </div>
      )}

      {cargando || !form ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.25 max-w-3xl">
          <div className="grid gap-4.5 sm:grid-cols-2">
            <Field label="Nombre" htmlFor="plan-nombre">
              <Input id="plan-nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            </Field>
            <Field label="Precio mensual (COP)" htmlFor="plan-precio">
              <Input
                id="plan-precio"
                inputMode="decimal"
                value={form.precioMensualCop}
                onChange={(e) => setForm({ ...form, precioMensualCop: e.target.value })}
              />
            </Field>
            <Field label="Límite de filas por importación" htmlFor="plan-filas">
              <Input
                id="plan-filas"
                type="number"
                value={form.limiteFilasImportacion}
                onChange={(e) => setForm({ ...form, limiteFilasImportacion: Number(e.target.value) })}
              />
            </Field>
            <Field label="Mensajes marketing incluidos" htmlFor="plan-incluidos">
              <Input
                id="plan-incluidos"
                type="number"
                value={form.mensajesMarketingIncluidos}
                onChange={(e) => setForm({ ...form, mensajesMarketingIncluidos: Number(e.target.value) })}
              />
            </Field>
            <Field label="Precio marketing / mensaje (COP)" htmlFor="plan-precio-mkt">
              <Input
                id="plan-precio-mkt"
                inputMode="decimal"
                value={form.precioMarketingMensajeCop}
                onChange={(e) => setForm({ ...form, precioMarketingMensajeCop: e.target.value })}
              />
            </Field>
            <Field label="Precio utility / mensaje (COP)" htmlFor="plan-precio-util">
              <Input
                id="plan-precio-util"
                inputMode="decimal"
                value={form.precioUtilityMensajeCop}
                onChange={(e) => setForm({ ...form, precioUtilityMensajeCop: e.target.value })}
              />
            </Field>
            <Field label="Usuarios incluidos" htmlFor="plan-usuarios">
              <Input
                id="plan-usuarios"
                type="number"
                value={form.maxUsuarios}
                onChange={(e) => setForm({ ...form, maxUsuarios: Number(e.target.value) })}
              />
            </Field>
            <Field label="Números de WhatsApp incluidos" htmlFor="plan-whatsapp">
              <Input
                id="plan-whatsapp"
                type="number"
                value={form.maxWhatsappNumeros}
                onChange={(e) => setForm({ ...form, maxWhatsappNumeros: Number(e.target.value) })}
              />
            </Field>
          </div>
          <Button onClick={guardar} loading={guardando} className="mt-4.5">
            Guardar cambios
          </Button>
        </div>
      )}
    </AppShell>
  );
};
