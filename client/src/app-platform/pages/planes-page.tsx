import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { Landmark, Plus } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { EmptyState } from "../../ui/components/empty-state";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Spinner } from "../../ui/components/spinner";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { usePlanes } from "../hooks/use-planes";
import type { Plan, PlanRequest } from "../types/plan";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };

const VACIO: PlanRequest = {
  nombre: "",
  precioMensualCop: "",
  limiteFilasImportacion: 0,
  mensajesMarketingIncluidos: 0,
  precioMarketingMensajeCop: "",
  precioUtilityMensajeCop: "",
  maxUsuarios: 0,
  maxWhatsappNumeros: 0,
};

export const PlanesPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, cerrarSesion } = useAuth();
  const { listarPlanes, crearPlan } = usePlanes();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [planes, setPlanes] = useState<Plan[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [creando, setCreando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [form, setForm] = useState<PlanRequest>(VACIO);

  const cargar = useCallback(
    () =>
      listarPlanes()
        .then(setPlanes)
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar los planes."))
        .finally(() => setCargando(false)),
    [listarPlanes],
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

  const guardar = async () => {
    setError(null);
    setGuardando(true);
    try {
      await crearPlan(form);
      setForm(VACIO);
      setCreando(false);
      await cargar();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear el plan.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      activeHref="/app-platform/planes"
      pageTitle="Planes"
      logoLabel="Pulso"
      tenantNombre={usuario?.tenantNombre ?? ""}
      planNombre="Administrador del sistema"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
      userRolLabel={usuario ? ROL_LABEL[usuario.rol] : ""}
      onCerrarSesion={salir}
      esSuperadmin
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
        <div>
          <h1 className="text-[22px] mb-1">Planes</h1>
          <p className="text-ink-2 text-sm">Precio, límites e incluidos de cada plan comercial.</p>
        </div>
        <Button onClick={() => setCreando((v) => !v)}>
          <Plus className="size-4" aria-hidden />
          Nuevo plan
        </Button>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {creando && (
        <div className="bg-surface border border-border rounded-md p-4.25 mb-5 max-w-3xl">
          <div className="grid gap-4.5 sm:grid-cols-2">
            <Field label="Nombre" htmlFor="plan-nombre">
              <Input
                id="plan-nombre"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
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
          <div className="flex gap-2.5 mt-4.5">
            <Button onClick={guardar} loading={guardando} disabled={form.nombre.trim() === ""}>
              Guardar plan
            </Button>
            <Button variant="ghost" onClick={() => setCreando(false)}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : planes.length === 0 ? (
        <EmptyState icon={Landmark} title="Todavía no hay planes" description="Crea el primer plan comercial." />
      ) : (
        <>
          <div className="flex flex-col gap-2.5 md:hidden">
            {planes.map((plan) => (
              <button
                key={plan.publicId}
                type="button"
                onClick={() => navigate(`/app-platform/planes/${plan.publicId}`)}
                className="border border-border rounded-md p-3.5 text-left bg-surface"
              >
                <div className="font-semibold">{plan.nombre}</div>
                <div className="text-ink-2 text-sm mt-1">${plan.precioMensualCop}/mes</div>
                <div className="text-ink-3 text-xs mt-1.5">
                  {plan.mensajesMarketingIncluidos} incluidos · {plan.maxUsuarios} usuarios · {plan.maxWhatsappNumeros}{" "}
                  números WhatsApp
                </div>
              </button>
            ))}
          </div>

          <div className="hidden md:block">
            <Table>
              <thead>
                <tr>
                  <TableHeadCell>Nombre</TableHeadCell>
                  <TableHeadCell>Precio mensual</TableHeadCell>
                  <TableHeadCell>Incluidos marketing</TableHeadCell>
                  <TableHeadCell>Usuarios</TableHeadCell>
                  <TableHeadCell>Números WhatsApp</TableHeadCell>
                </tr>
              </thead>
              <tbody>
                {planes.map((plan) => (
                  <tr
                    key={plan.publicId}
                    className="cursor-pointer hover:bg-surface-2"
                    onClick={() => navigate(`/app-platform/planes/${plan.publicId}`)}
                  >
                    <TableCell className="font-semibold">{plan.nombre}</TableCell>
                    <TableCell>${plan.precioMensualCop}</TableCell>
                    <TableCell>{plan.mensajesMarketingIncluidos}</TableCell>
                    <TableCell>{plan.maxUsuarios}</TableCell>
                    <TableCell>{plan.maxWhatsappNumeros}</TableCell>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </>
      )}
    </AppShell>
  );
};
