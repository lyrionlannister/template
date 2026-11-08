import { useEffect, useRef, useState, type FC } from "react";
import { useNavigate } from "react-router";
import { AlertTriangle, CheckCircle2, Settings, Users } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { FileDropzone } from "../../ui/components/file-dropzone";
import { Input } from "../../ui/components/input";
import { Select } from "../../ui/components/select";
import { Spinner } from "../../ui/components/spinner";
import { Stepper } from "../../ui/components/stepper";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { useContacts } from "../hooks/use-contacts";
import type { ContactoRechazado, EstadoImportacionDetalle, PrevisualizacionImportacion } from "../types/importacion";

const NAV_ITEMS = [
  { label: "Contactos", href: "/contactos", icon: Users },
  { label: "Ajustes", href: "/ajustes", icon: Settings },
];

const PASOS = [{ label: "Subir archivo" }, { label: "Mapear columnas" }, { label: "Resultado" }];
const INTERVALO_POLLING_MS = 1500;
const RECHAZOS_POR_PAGINA = 20;

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

const adivinarColumnaTelefono = (columnas: string[]): string =>
  columnas.find((columna) => columna.toLowerCase().includes("telefono")) ?? columnas[0] ?? "";

export const ImportarContactosPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual } = useAuth();
  const { previsualizarImportacion, confirmarImportacion, obtenerEstadoImportacion, listarRechazosDeImportacion } =
    useContacts();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [paso, setPaso] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [previsualizacion, setPrevisualizacion] = useState<PrevisualizacionImportacion | null>(null);
  const [columnaTelefono, setColumnaTelefono] = useState("");
  const [mapeoVariables, setMapeoVariables] = useState<Record<string, string>>({});
  const [confirmando, setConfirmando] = useState(false);

  const [importacion, setImportacion] = useState<EstadoImportacionDetalle | null>(null);
  const [rechazos, setRechazos] = useState<ContactoRechazado[]>([]);
  const [paginaRechazos, setPaginaRechazos] = useState(1);
  const [totalRechazos, setTotalRechazos] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    obtenerSesionActual()
      .then(setUsuario)
      .catch(() => setUsuario(null));
  }, [obtenerSesionActual]);

  useEffect(() => () => {
    if (pollingRef.current) clearTimeout(pollingRef.current);
  }, []);

  const subirArchivo = async (files: FileList) => {
    const archivo = files[0];
    if (!archivo) return;
    setError(null);
    try {
      const resultado = await previsualizarImportacion(archivo);
      setPrevisualizacion(resultado);
      const telefono = adivinarColumnaTelefono(resultado.columnas);
      setColumnaTelefono(telefono);
      setMapeoVariables(
        Object.fromEntries(resultado.columnas.filter((columna) => columna !== telefono).map((columna) => [columna, columna])),
      );
      setPaso(1);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo leer el archivo.");
    }
  };

  const pollearImportacion = async (publicId: string) => {
    const estado = await obtenerEstadoImportacion(publicId);
    setImportacion(estado);
    if (estado.estado === "pendiente" || estado.estado === "procesando") {
      pollingRef.current = setTimeout(() => pollearImportacion(publicId), INTERVALO_POLLING_MS);
      return;
    }
    if (estado.filasRechazadas > 0) {
      const primeraPagina = await listarRechazosDeImportacion(publicId, 1, RECHAZOS_POR_PAGINA);
      setRechazos(primeraPagina.rechazos);
      setTotalRechazos(primeraPagina.total);
      setPaginaRechazos(1);
    }
  };

  const confirmar = async () => {
    if (!previsualizacion) return;
    setConfirmando(true);
    setError(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(mapeoVariables).filter(([columna, variable]) => columna !== columnaTelefono && variable.trim()),
      );
      const creada = await confirmarImportacion({
        previewId: previsualizacion.previewId,
        columnaTelefono,
        mapeoVariables: payload,
      });
      setPaso(2);
      await pollearImportacion(creada.publicId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo confirmar la importación.");
    } finally {
      setConfirmando(false);
    }
  };

  const cambiarPaginaRechazos = async (nuevaPagina: number) => {
    if (!importacion) return;
    const pagina = await listarRechazosDeImportacion(importacion.publicId, nuevaPagina, RECHAZOS_POR_PAGINA);
    setRechazos(pagina.rechazos);
    setPaginaRechazos(nuevaPagina);
  };

  const reiniciar = () => {
    if (pollingRef.current) clearTimeout(pollingRef.current);
    setPrevisualizacion(null);
    setImportacion(null);
    setRechazos([]);
    setTotalRechazos(0);
    setPaginaRechazos(1);
    setError(null);
    setPaso(0);
  };

  const procesando = importacion ? importacion.estado === "pendiente" || importacion.estado === "procesando" : false;

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
          <h1 className="text-[22px] mb-1">Importar contactos</h1>
          <p className="text-ink-2 text-sm">Sube un archivo CSV, XLSX o Parquet.</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => navigate("/contactos")}>
          Volver al listado
        </Button>
      </div>

      <Stepper steps={PASOS} currentIndex={paso} />

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="bg-surface border border-border rounded-md p-4.75 max-w-3xl">
        {paso === 0 && (
          <FileDropzone
            label="Arrastra tu archivo aquí o haz clic para elegirlo"
            hint="CSV, XLSX o Parquet. El límite de filas depende de tu plan."
            accept=".csv,.xlsx,.parquet"
            onFilesSelected={subirArchivo}
          />
        )}

        {paso === 1 && previsualizacion && (
          <>
            <p className="text-ink-2 text-sm mb-4.5">
              {previsualizacion.totalFilas.toLocaleString("es-CO")} filas detectadas. Revisa el mapeo antes de
              importar.
            </p>

            <Field label="Columna de teléfono" htmlFor="columna-telefono" hint="Debe venir en formato internacional, con +.">
              <Select
                id="columna-telefono"
                value={columnaTelefono}
                onChange={(event) => setColumnaTelefono(event.target.value)}
                options={previsualizacion.columnas.map((columna) => ({ value: columna, label: columna }))}
              />
            </Field>

            <h3 className="text-[14.5px] font-semibold mt-5 mb-2.5">Columnas a importar como variables</h3>
            <div className="flex flex-col gap-3 mb-5">
              {previsualizacion.columnas
                .filter((columna) => columna !== columnaTelefono)
                .map((columna) => (
                  <div key={columna} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-3 items-center">
                    <span className="text-sm text-ink-2 truncate">{columna}</span>
                    <Input
                      value={mapeoVariables[columna] ?? ""}
                      placeholder="No importar esta columna"
                      onChange={(event) =>
                        setMapeoVariables((actual) => ({ ...actual, [columna]: event.target.value }))
                      }
                    />
                  </div>
                ))}
            </div>

            <h3 className="text-[14.5px] font-semibold mb-2.5">Primeras filas</h3>

            {/* Mobile: tarjetas, nunca la tabla con scroll horizontal (ver skill responsive-mobile-first). */}
            <div className="flex flex-col gap-2.5 mb-5 md:hidden">
              {previsualizacion.muestra.map((fila, indice) => (
                <div key={indice} className="border border-border rounded-md p-3 text-sm">
                  {previsualizacion.columnas.map((columna) => (
                    <div key={columna} className="flex justify-between gap-3 py-0.5">
                      <span className="text-ink-3 text-xs">{columna}</span>
                      <span className="truncate">{fila[columna]}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            <div className="hidden md:block mb-5">
              <Table>
                <thead>
                  <tr>
                    {previsualizacion.columnas.map((columna) => (
                      <TableHeadCell key={columna}>{columna}</TableHeadCell>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previsualizacion.muestra.map((fila, indice) => (
                    <tr key={indice}>
                      {previsualizacion.columnas.map((columna) => (
                        <TableCell key={columna}>{fila[columna]}</TableCell>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <div className="flex gap-3 flex-wrap">
              <Button variant="ghost" onClick={reiniciar}>
                Elegir otro archivo
              </Button>
              <Button onClick={confirmar} loading={confirmando} disabled={!columnaTelefono}>
                Confirmar e importar
              </Button>
            </div>
          </>
        )}

        {paso === 2 && (
          <>
            {procesando || !importacion ? (
              <div className="flex items-center gap-2.5 text-ink-2 py-8 justify-center">
                <Spinner /> Importando contactos…
              </div>
            ) : importacion.estado === "fallida" ? (
              <Alert variant="err" title="La importación falló">
                {importacion.motivoFallo ?? "No se registró un motivo."}
              </Alert>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
                  <div>
                    <span className="text-xs text-ink-3">Total filas</span>
                    <div className="font-semibold text-lg">{importacion.totalFilas.toLocaleString("es-CO")}</div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Aceptadas</span>
                    <div className="font-semibold text-lg text-ok-ink">
                      {importacion.filasAceptadas.toLocaleString("es-CO")}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Rechazadas</span>
                    <div className="font-semibold text-lg text-err-ink">
                      {importacion.filasRechazadas.toLocaleString("es-CO")}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Con advertencia</span>
                    <div className="font-semibold text-lg text-warn-ink">
                      {importacion.filasConAdvertencia.toLocaleString("es-CO")}
                    </div>
                  </div>
                </div>

                {importacion.filasRechazadas === 0 ? (
                  <Alert variant="ok" title="Importación completada">
                    Todas las filas se aceptaron.
                  </Alert>
                ) : (
                  <>
                    <h3 className="text-[14.5px] font-semibold mb-2.5 flex items-center gap-1.5">
                      <AlertTriangle className="size-4 text-err" aria-hidden />
                      Filas rechazadas
                    </h3>

                    <div className="flex flex-col gap-2.5 mb-3.5">
                      {rechazos.map((rechazo, indice) => (
                        <div key={indice} className="border border-border rounded-md p-3 text-sm">
                          <div className="text-err-ink font-medium mb-1">{rechazo.motivo}</div>
                          <div className="text-ink-3 text-xs break-all">{JSON.stringify(rechazo.filaCruda)}</div>
                        </div>
                      ))}
                    </div>

                    {totalRechazos > RECHAZOS_POR_PAGINA && (
                      <div className="flex items-center gap-2.5 mb-3.5">
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={paginaRechazos <= 1}
                          onClick={() => cambiarPaginaRechazos(paginaRechazos - 1)}
                        >
                          Anterior
                        </Button>
                        <span className="text-xs text-ink-3">
                          Página {paginaRechazos} de {Math.ceil(totalRechazos / RECHAZOS_POR_PAGINA)}
                        </span>
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={paginaRechazos >= Math.ceil(totalRechazos / RECHAZOS_POR_PAGINA)}
                          onClick={() => cambiarPaginaRechazos(paginaRechazos + 1)}
                        >
                          Siguiente
                        </Button>
                      </div>
                    )}
                  </>
                )}

                <div className="flex gap-3 flex-wrap mt-4.5">
                  <Button variant="ghost" onClick={reiniciar}>
                    Importar otro archivo
                  </Button>
                  <Button onClick={() => navigate("/contactos")}>
                    <CheckCircle2 className="size-4" aria-hidden />
                    Ver contactos
                  </Button>
                </div>
              </>
            )}
          </>
        )}

      </div>
    </AppShell>
  );
};
