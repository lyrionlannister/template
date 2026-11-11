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
import { Spinner } from "../../ui/components/spinner";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { useTipoCambio } from "../hooks/use-tipo-cambio";
import type { TipoCambio } from "../types/tipo-cambio";

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();
const ROL_LABEL: Record<Usuario["rol"], string> = { administrador: "Administrador", miembro: "Miembro" };
const HOY = () => new Date().toISOString().slice(0, 10);
const PAR = "USD/COP";

export const TipoCambioPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual, cerrarSesion } = useAuth();
  const { registrar, historico, vigente } = useTipoCambio();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [registros, setRegistros] = useState<TipoCambio[]>([]);
  const [valorVigente, setValorVigente] = useState<TipoCambio | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nuevoValor, setNuevoValor] = useState("");
  const [nuevaFuente, setNuevaFuente] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(
    () =>
      Promise.all([historico(PAR), vigente(PAR)])
        .then(([lista, actual]) => {
          setRegistros(lista);
          setValorVigente(actual);
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la TRM."))
        .finally(() => setCargando(false)),
    [historico, vigente],
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
      await registrar({ par: PAR, valor: nuevoValor, fuente: nuevaFuente, vigenteDesde: HOY() });
      setNuevoValor("");
      setNuevaFuente("");
      await cargar();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar la TRM.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <AppShell
      activeHref="/app-platform/tipo-cambio"
      pageTitle="Tipo de cambio"
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
        <h1 className="text-[22px] mb-1">Tipo de cambio</h1>
        <p className="text-ink-2 text-sm">TRM {PAR}, versionada por vigencia.</p>
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
      ) : (
        <>
          <div className="bg-surface border border-border rounded-md p-4.25 mb-5 max-w-xl">
            <h3 className="font-semibold text-[15px] mb-3">Vigente</h3>
            {valorVigente ? (
              <p className="text-2xl font-bold">
                ${valorVigente.valor}
                <span className="text-ink-3 text-xs font-normal ml-2">desde {valorVigente.vigenteDesde}</span>
              </p>
            ) : (
              <p className="text-ink-2 text-sm">Sin TRM vigente registrada.</p>
            )}

            <div className="grid gap-4.5 sm:grid-cols-[1fr_1fr_auto] mt-4.5 items-end">
              <Field label="Nuevo valor (COP por USD)" htmlFor="trm-valor">
                <Input id="trm-valor" inputMode="decimal" value={nuevoValor} onChange={(e) => setNuevoValor(e.target.value)} />
              </Field>
              <Field label="Fuente" htmlFor="trm-fuente">
                <Input id="trm-fuente" value={nuevaFuente} onChange={(e) => setNuevaFuente(e.target.value)} />
              </Field>
              <Button onClick={guardar} loading={guardando} disabled={nuevoValor.trim() === "" || nuevaFuente.trim() === ""}>
                Registrar
              </Button>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 md:hidden">
            {registros.map((r) => (
              <div key={r.publicId} className="border border-border rounded-md p-3.5 bg-surface">
                <div className="font-semibold">${r.valor}</div>
                <div className="text-ink-2 text-sm mt-1">{r.fuente}</div>
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
                  <TableHeadCell>Valor</TableHeadCell>
                  <TableHeadCell>Fuente</TableHeadCell>
                  <TableHeadCell>Vigente desde</TableHeadCell>
                  <TableHeadCell>Vigente hasta</TableHeadCell>
                </tr>
              </thead>
              <tbody>
                {registros.map((r) => (
                  <tr key={r.publicId}>
                    <TableCell className="font-semibold">${r.valor}</TableCell>
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
