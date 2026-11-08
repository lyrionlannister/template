import { useCallback, useEffect, useState, type FC, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { RotateCcw, Search, Settings, Upload, Users } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { EmptyState } from "../../ui/components/empty-state";
import { Input } from "../../ui/components/input";
import { JsonViewer } from "../../ui/components/json-viewer";
import { Modal } from "../../ui/components/modal";
import { Pill } from "../../ui/components/pill";
import { Spinner } from "../../ui/components/spinner";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { Toolbar } from "../../ui/components/toolbar";
import { useContacts } from "../hooks/use-contacts";
import type { ConflictoVariable } from "../types/conflicto";
import type { Contacto } from "../types/contacto";

const NAV_ITEMS = [
  { label: "Contactos", href: "/contactos", icon: Users },
  { label: "Ajustes", href: "/ajustes", icon: Settings },
];

const POR_PAGINA = 20;

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

const formatFechaHora = (iso: string): string => new Date(iso).toLocaleDateString("es-CO");

export const ContactosPage: FC = () => {
  const navigate = useNavigate();
  const { obtenerSesionActual } = useAuth();
  const { listarContactos, obtenerContacto, listarConflictosDeContacto, revertirConflicto } = useContacts();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [contactos, setContactos] = useState<Contacto[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [busqueda, setBusqueda] = useState("");
  const [telefonoAplicado, setTelefonoAplicado] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [contactoAbierto, setContactoAbierto] = useState<Contacto | null>(null);
  const [conflictos, setConflictos] = useState<ConflictoVariable[]>([]);
  const [cargandoConflictos, setCargandoConflictos] = useState(false);
  const [revirtiendo, setRevirtiendo] = useState<string | null>(null);

  const cargar = useCallback(
    (paginaAConsultar: number, telefono: string) => {
      setCargando(true);
      return listarContactos(paginaAConsultar, POR_PAGINA, telefono)
        .then((resultado) => {
          setContactos(resultado.contactos);
          setTotal(resultado.total);
          setPagina(resultado.pagina);
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar los contactos."))
        .finally(() => setCargando(false));
    },
    [listarContactos],
  );

  useEffect(() => {
    obtenerSesionActual()
      .then(setUsuario)
      .catch(() => setUsuario(null));
  }, [obtenerSesionActual]);

  useEffect(() => {
    cargar(1, "");
  }, [cargar]);

  const buscar = (event: FormEvent) => {
    event.preventDefault();
    setTelefonoAplicado(busqueda);
    cargar(1, busqueda);
  };

  const abrirContacto = async (contacto: Contacto) => {
    setContactoAbierto(contacto);
    setConflictos([]);
    setCargandoConflictos(true);
    try {
      const detalle = await obtenerContacto(contacto.publicId);
      setContactoAbierto(detalle);
      const listaConflictos = await listarConflictosDeContacto(contacto.publicId);
      setConflictos(listaConflictos);
    } catch {
      // El modal ya muestra lo que trae el listado; un fallo aquí solo deja los conflictos vacíos.
    } finally {
      setCargandoConflictos(false);
    }
  };

  const revertir = async (conflicto: ConflictoVariable) => {
    if (!contactoAbierto) return;
    setRevirtiendo(conflicto.publicId);
    try {
      await revertirConflicto(conflicto.publicId);
      setContactoAbierto(await obtenerContacto(contactoAbierto.publicId));
      setConflictos(await listarConflictosDeContacto(contactoAbierto.publicId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo revertir este conflicto.");
    } finally {
      setRevirtiendo(null);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));

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
          <h1 className="text-[22px] mb-1">Contactos</h1>
          <p className="text-ink-2 text-sm">{total.toLocaleString("es-CO")} contactos en total.</p>
        </div>
        <div className="flex gap-2.5 flex-wrap">
          <Button variant="secondary" onClick={() => navigate("/contactos/configuracion")}>
            <Settings className="size-4" aria-hidden />
            Configuración
          </Button>
          <Button onClick={() => navigate("/contactos/importar")}>
            <Upload className="size-4" aria-hidden />
            Importar contactos
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4.5">
          <Alert variant="err" title="Algo salió mal" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="bg-surface border border-border rounded-md">
        <Toolbar>
          <form onSubmit={buscar} className="flex gap-2.5 flex-1 min-w-0">
            <Input
              value={busqueda}
              onChange={(event) => setBusqueda(event.target.value)}
              placeholder="Buscar por teléfono…"
              className="max-w-sm"
            />
            <Button type="submit" variant="secondary" size="sm">
              <Search className="size-4" aria-hidden />
              Buscar
            </Button>
          </form>
        </Toolbar>

        {cargando ? (
          <div className="grid place-items-center py-16">
            <Spinner />
          </div>
        ) : contactos.length === 0 ? (
          <div className="py-10">
            <EmptyState
              icon={Users}
              title={telefonoAplicado ? "Sin resultados" : "Todavía no hay contactos"}
              description={
                telefonoAplicado
                  ? "Ningún teléfono coincide con esa búsqueda."
                  : "Importa un archivo para empezar a cargar contactos."
              }
              action={
                !telefonoAplicado && (
                  <Button onClick={() => navigate("/contactos/importar")}>Importar contactos</Button>
                )
              }
            />
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-2.5 p-4 md:hidden">
              {contactos.map((contacto) => (
                <button
                  key={contacto.publicId}
                  type="button"
                  onClick={() => abrirContacto(contacto)}
                  className="border border-border rounded-md p-3.5 text-left"
                >
                  <div className="font-semibold">{contacto.telefono}</div>
                  <div className="text-ink-3 text-xs mt-1">
                    {Object.keys(contacto.variables).length} variables · {formatFechaHora(contacto.creadoEn)}
                  </div>
                </button>
              ))}
            </div>

            <div className="hidden md:block p-4">
              <Table>
                <thead>
                  <tr>
                    <TableHeadCell>Teléfono</TableHeadCell>
                    <TableHeadCell>Variables</TableHeadCell>
                    <TableHeadCell>Creado</TableHeadCell>
                  </tr>
                </thead>
                <tbody>
                  {contactos.map((contacto) => (
                    <tr
                      key={contacto.publicId}
                      onClick={() => abrirContacto(contacto)}
                      className="cursor-pointer hover:bg-surface-2"
                    >
                      <TableCell>{contacto.telefono}</TableCell>
                      <TableCell>{Object.keys(contacto.variables).length}</TableCell>
                      <TableCell>{formatFechaHora(contacto.creadoEn)}</TableCell>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <div className="flex items-center gap-2.5 p-4 border-t border-border">
              <Button
                variant="secondary"
                size="sm"
                disabled={pagina <= 1}
                onClick={() => cargar(pagina - 1, telefonoAplicado)}
              >
                Anterior
              </Button>
              <span className="text-xs text-ink-3">
                Página {pagina} de {totalPaginas}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={pagina >= totalPaginas}
                onClick={() => cargar(pagina + 1, telefonoAplicado)}
              >
                Siguiente
              </Button>
            </div>
          </>
        )}
      </div>

      <Modal
        open={contactoAbierto !== null}
        onClose={() => setContactoAbierto(null)}
        title={contactoAbierto?.telefono ?? ""}
        description="Variables importadas y conflictos registrados para este contacto."
      >
        {contactoAbierto && (
          <div className="mt-4">
            <JsonViewer value={contactoAbierto.variables} />

            <h4 className="text-[13.5px] font-semibold mt-5 mb-2.5">Conflictos de variables</h4>
            {cargandoConflictos ? (
              <div className="flex justify-center py-4">
                <Spinner />
              </div>
            ) : conflictos.length === 0 ? (
              <p className="text-ink-3 text-sm">Sin conflictos registrados.</p>
            ) : (
              <div className="flex flex-col gap-2.5 max-h-60 overflow-y-auto">
                {conflictos.map((conflicto) => (
                  <div key={conflicto.publicId} className="border border-border rounded-md p-3 text-sm">
                    <div className="flex items-center justify-between gap-2.5 mb-1">
                      <span className="font-semibold">{conflicto.clave}</span>
                      {conflicto.revertidoEn ? (
                        <Pill variant="neutral">Revertido</Pill>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          loading={revirtiendo === conflicto.publicId}
                          onClick={() => revertir(conflicto)}
                        >
                          <RotateCcw className="size-3.5" aria-hidden />
                          Revertir
                        </Button>
                      )}
                    </div>
                    <div className="text-ink-2 text-xs">
                      "{conflicto.valorAnterior}" → "{conflicto.valorNuevo}"
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </AppShell>
  );
};
