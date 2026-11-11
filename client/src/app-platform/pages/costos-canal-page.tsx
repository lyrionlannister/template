import { useCallback, useEffect, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Select } from "../../ui/components/select";
import { Spinner } from "../../ui/components/spinner";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { CANAL_LABEL, CATEGORIA_LABEL } from "../const/labels";
import { useCostosCanal } from "../hooks/use-costos-canal";
import type { CanalMensajeria, CategoriaMensaje, CostoCanal } from "../types/costo-canal";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };
const HOY = () => new Date().toISOString().slice(0, 10);

const CANALES: CanalMensajeria[] = ["whatsapp", "sms", "rcs"];
const CATEGORIAS: CategoriaMensaje[] = ["marketing", "utility", "authentication", "service"];

export const CostosCanalPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, cerrarSesion } = useAuth();
  const { registrar, historico, vigente } = useCostosCanal();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [canal, setCanal] = useState<CanalMensajeria>("whatsapp");
  const [categoria, setCategoria] = useState<CategoriaMensaje>("marketing");
  const [registros, setRegistros] = useState<CostoCanal[]>([]);
  const [costoVigente, setCostoVigente] = useState<CostoCanal | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [proveedor, setProveedor] = useState("");
  const [costoUnitario, setCostoUnitario] = useState("");
  const [moneda, setMoneda] = useState("COP");
  const [fuente, setFuente] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(
    (c: CanalMensajeria, cat: CategoriaMensaje) => {
      setCargando(true);
      return Promise.all([historico(c, cat), vigente(c, cat)])
        .then(([lista, actual]) => {
          setRegistros(lista);
          setCostoVigente(actual);
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el costo."))
        .finally(() => setCargando(false));
    },
    [historico, vigente],
  );

  useEffect(() => {
    obtenerSesionActual()
      .then(setUsuario)
      .catch(() => setUsuario(null));
  }, [obtenerSesionActual]);

  useEffect(() => {
    cargar(canal, categoria);
  }, [canal, categoria, cargar]);

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  const guardar = async () => {
    setError(null);
    setGuardando(true);
    try {
      await registrar({
        canal,
        categoria,
        proveedor: proveedor.trim(),
        costoUnitario,
        moneda,
        vigenteDesde: HOY(),
        fuente: fuente.trim(),
      });
      setCostoUnitario("");
      setFuente("");
      await cargar(canal, categoria);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar el costo.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      activeHref="/app-platform/costos-canal"
      pageTitle="Costos por canal"
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
        <h1 className="text-[22px] mb-1">Costos por canal</h1>
        <p className="text-ink-2 text-sm">Histórico de costo de proveedor, versionado por vigencia. Nunca se sobrescribe.</p>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="grid gap-4.5 sm:grid-cols-2 max-w-xl mb-5">
        <Field label="Canal" htmlFor="costo-canal">
          <Select
            id="costo-canal"
            value={canal}
            onChange={(e) => setCanal(e.target.value as CanalMensajeria)}
            options={CANALES.map((c) => ({ value: c, label: CANAL_LABEL[c] }))}
          />
        </Field>
        <Field label="Categoría" htmlFor="costo-categoria">
          <Select
            id="costo-categoria"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value as CategoriaMensaje)}
            options={CATEGORIAS.map((c) => ({ value: c, label: CATEGORIA_LABEL[c] }))}
          />
        </Field>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : (
        <>
          <div className="bg-surface border border-border rounded-md p-4.25 mb-5 max-w-3xl">
            <h3 className="font-semibold text-[15px] mb-3">Vigente</h3>
            {costoVigente ? (
              <p className="text-2xl font-bold">
                {costoVigente.costoUnitario} {costoVigente.moneda}
                <span className="text-ink-3 text-xs font-normal ml-2">
                  {costoVigente.proveedor} · desde {costoVigente.vigenteDesde}
                </span>
              </p>
            ) : (
              <p className="text-ink-2 text-sm">Sin costo vigente registrado para esta combinación.</p>
            )}

            <div className="grid gap-4.5 sm:grid-cols-2 lg:grid-cols-4 mt-4.5 items-end">
              <Field label="Proveedor" htmlFor="costo-proveedor">
                <Input id="costo-proveedor" value={proveedor} onChange={(e) => setProveedor(e.target.value)} />
              </Field>
              <Field label="Costo unitario" htmlFor="costo-valor">
                <Input id="costo-valor" inputMode="decimal" value={costoUnitario} onChange={(e) => setCostoUnitario(e.target.value)} />
              </Field>
              <Field label="Moneda" htmlFor="costo-moneda">
                <Input id="costo-moneda" value={moneda} onChange={(e) => setMoneda(e.target.value)} />
              </Field>
              <Field label="Fuente" htmlFor="costo-fuente">
                <Input id="costo-fuente" value={fuente} onChange={(e) => setFuente(e.target.value)} />
              </Field>
            </div>
            <Button
              onClick={guardar}
              loading={guardando}
              disabled={proveedor.trim() === "" || costoUnitario.trim() === "" || fuente.trim() === ""}
              className="mt-4"
            >
              Registrar costo
            </Button>
          </div>

          <div className="flex flex-col gap-2.5 md:hidden">
            {registros.map((r) => (
              <div key={r.publicId} className="border border-border rounded-md p-3.5 bg-surface">
                <div className="font-semibold">{r.proveedor}</div>
                <div className="text-ink-2 text-sm mt-1">
                  {r.costoUnitario} {r.moneda} · {r.fuente}
                </div>
                <div className="text-ink-3 text-xs mt-1.5">
                  {r.vigenteDesde} → {r.vigenteHasta ?? "vigente"}
                </div>
              </div>
            ))}
          </div>

          <div className="hidden md:block">
            <Table>
              <thead>
                <tr>
                  <TableHeadCell>Proveedor</TableHeadCell>
                  <TableHeadCell>Costo</TableHeadCell>
                  <TableHeadCell>Fuente</TableHeadCell>
                  <TableHeadCell>Vigente desde</TableHeadCell>
                  <TableHeadCell>Vigente hasta</TableHeadCell>
                </tr>
              </thead>
              <tbody>
                {registros.map((r) => (
                  <tr key={r.publicId}>
                    <TableCell className="font-semibold">{r.proveedor}</TableCell>
                    <TableCell>
                      {r.costoUnitario} {r.moneda}
                    </TableCell>
                    <TableCell>{r.fuente}</TableCell>
                    <TableCell>{r.vigenteDesde}</TableCell>
                    <TableCell>{r.vigenteHasta ?? "—"}</TableCell>
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
