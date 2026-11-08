import { useCallback, useEffect, useState, type FC, type FormEvent } from "react";
import { CreditCard, Landmark, Settings, Smartphone, Users, Wallet } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { formatCop } from "../../shared/utils/format-cop";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Pill } from "../../ui/components/pill";
import { SegmentedControl } from "../../ui/components/segmented-control";
import { Select } from "../../ui/components/select";
import { Spinner } from "../../ui/components/spinner";
import { Table } from "../../ui/components/table";
import { TableCell } from "../../ui/components/table-cell";
import { TableHeadCell } from "../../ui/components/table-head-cell";
import { TarjetaVisual } from "../../ui/components/tarjeta-visual";
import { BancoVisual } from "../../ui/components/banco-visual";
import { NequiVisual } from "../../ui/components/nequi-visual";
import { SecureStrip } from "../../ui/components/secure-strip";
import { detectarMarcaTarjeta } from "../../shared/utils/detectar-marca-tarjeta";
import { useBilling } from "../hooks/use-billing";
import { useWompiTokenizacion } from "../hooks/use-wompi-tokenizacion";
import type { TokensDeAceptacion } from "../types/fuente-de-pago";
import type { EstadoMovimiento, InstitucionFinanciera, MedioRecarga, SaldoEstado } from "../types/saldo";

const NAV_ITEMS = [
  { label: "Contactos", href: "/contactos", icon: Users },
  { label: "Ajustes", href: "/ajustes", icon: Settings },
];

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

const MAX_INTENTOS_POLLING = 30;
const INTERVALO_POLLING_MS = 2000;

const ESTADO_PILL: Record<EstadoMovimiento, { variant: "ok" | "warn" | "err"; label: string }> = {
  aprobada: { variant: "ok", label: "Aprobada" },
  pendiente: { variant: "warn", label: "Pendiente" },
  rechazada: { variant: "err", label: "Rechazada" },
  error: { variant: "err", label: "Error" },
};

export const SaldoPage: FC = () => {
  const { obtenerSesionActual } = useAuth();
  const {
    obtenerEstadoSaldo,
    obtenerTokensDeAceptacion,
    obtenerInstitucionesFinancieras,
    consultarEstadoMovimiento,
    recargarTarjeta,
    recargarPse,
    recargarNequi,
  } = useBilling();
  const { tokenizarTarjeta } = useWompiTokenizacion();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [saldo, setSaldo] = useState<SaldoEstado | null>(null);
  const [tokens, setTokens] = useState<TokensDeAceptacion | null>(null);
  const [instituciones, setInstituciones] = useState<InstitucionFinanciera[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const [medio, setMedio] = useState<MedioRecarga>("tarjeta");
  const [montoCop, setMontoCop] = useState("");

  const [numero, setNumero] = useState("");
  const [cvc, setCvc] = useState("");
  const [mesExpiracion, setMesExpiracion] = useState("");
  const [anioExpiracion, setAnioExpiracion] = useState("");
  const [titular, setTitular] = useState("");

  const [tipoPersona, setTipoPersona] = useState<"0" | "1">("0");
  const [tipoDocumento, setTipoDocumento] = useState("CC");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [bancoCode, setBancoCode] = useState("");

  const [telefonoNequi, setTelefonoNequi] = useState("");

  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [aceptaDatos, setAceptaDatos] = useState(false);

  const [recargando, setRecargando] = useState(false);
  const [errorRecarga, setErrorRecarga] = useState<string | null>(null);
  const [mensajeEspera, setMensajeEspera] = useState<string | null>(null);

  const cargarTodo = useCallback(() => {
    setCargando(true);
    return Promise.all([
      obtenerSesionActual(),
      obtenerEstadoSaldo(),
      obtenerTokensDeAceptacion(),
      obtenerInstitucionesFinancieras(),
    ])
      .then(([sesion, estadoSaldo, tokensDeAceptacion, listaInstituciones]) => {
        setUsuario(sesion);
        setSaldo(estadoSaldo);
        setTokens(tokensDeAceptacion);
        setInstituciones(listaInstituciones);
        if (!bancoCode && listaInstituciones.length > 0) setBancoCode(listaInstituciones[0].code);
      })
      .catch((err) => setErrorCarga(err instanceof Error ? err.message : "No se pudo cargar el saldo."))
      .finally(() => setCargando(false));
    // bancoCode se excluye a propósito: solo se usa como default inicial, no se quiere recargar al cambiarlo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [obtenerSesionActual, obtenerEstadoSaldo, obtenerTokensDeAceptacion, obtenerInstitucionesFinancieras]);

  useEffect(() => {
    cargarTodo();
  }, [cargarTodo]);

  const pollearMovimiento = useCallback(
    async (publicId: string) => {
      for (let intento = 0; intento < MAX_INTENTOS_POLLING; intento += 1) {
        const movimiento = await consultarEstadoMovimiento(publicId);
        if (movimiento.estado === "aprobada") {
          setMensajeEspera(null);
          setRecargando(false);
          await cargarTodo();
          return;
        }
        if (movimiento.estado === "rechazada" || movimiento.estado === "error") {
          setMensajeEspera(null);
          setRecargando(false);
          setErrorRecarga("La recarga no se pudo confirmar. Intenta de nuevo.");
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, INTERVALO_POLLING_MS));
      }
      setRecargando(false);
      setMensajeEspera(null);
      setErrorRecarga("La confirmación tardó demasiado. Revisa el historial en unos minutos.");
    },
    [consultarEstadoMovimiento, cargarTodo],
  );

  const recargar = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) return;
    const monto = Number(montoCop);
    if (!Number.isFinite(monto) || monto <= 0) return;

    setRecargando(true);
    setErrorRecarga(null);
    try {
      if (medio === "tarjeta") {
        const tarjeta = await tokenizarTarjeta({ numero, cvc, mesExpiracion, anioExpiracion, titular });
        const movimiento = await recargarTarjeta({
          montoCop: monto,
          token: tarjeta.token,
          acceptanceToken: tokens.acceptanceToken,
          acceptPersonalAuth: tokens.acceptPersonalAuth,
        });
        setMensajeEspera("Confirmando tu pago…");
        await pollearMovimiento(movimiento.publicId);
      } else if (medio === "pse") {
        const resultado = await recargarPse({
          montoCop: monto,
          userType: Number(tipoPersona),
          userLegalIdType: tipoDocumento,
          userLegalId: numeroDocumento,
          financialInstitutionCode: bancoCode,
        });
        if (resultado.asyncPaymentUrl) {
          window.open(resultado.asyncPaymentUrl, "_blank", "noopener,noreferrer");
          setMensajeEspera("Completa el pago en la ventana de tu banco. Verificando…");
        } else {
          setMensajeEspera("Confirmando tu pago…");
        }
        await pollearMovimiento(resultado.movimiento.publicId);
      } else {
        const movimiento = await recargarNequi({ montoCop: monto, phoneNumber: telefonoNequi });
        setMensajeEspera("Revisa la notificación en tu app Nequi y acéptala…");
        await pollearMovimiento(movimiento.publicId);
      }
    } catch (err) {
      setRecargando(false);
      setMensajeEspera(null);
      setErrorRecarga(err instanceof Error ? err.message : "No se pudo procesar la recarga.");
    }
  };

  const camposMedioValidos =
    medio === "tarjeta"
      ? numero.trim().length >= 13 &&
        cvc.trim().length >= 3 &&
        mesExpiracion.trim().length === 2 &&
        anioExpiracion.trim().length === 2 &&
        titular.trim().length > 0
      : medio === "pse"
        ? numeroDocumento.trim().length > 0 && bancoCode.trim().length > 0
        : telefonoNequi.trim().length === 10;

  const formularioValido =
    Number(montoCop) > 0 && camposMedioValidos && aceptaTerminos && aceptaDatos;

  return (
    <AppShell
      navItems={NAV_ITEMS}
      activeHref="/ajustes"
      logoLabel="Pulso"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Saldo</h1>
        <p className="text-ink-2 text-sm">Saldo utilizable para SMS y RCS.</p>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : errorCarga ? (
        <Alert variant="err" title="No se pudo cargar el saldo">
          {errorCarga}
        </Alert>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-5 items-start">
          <div className="flex flex-col gap-5 min-w-0 lg:order-1">
          <div className="bg-surface border border-border rounded-md p-4.75 w-full">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-3.5">
              <h3 className="text-[15px] font-semibold">Recargar saldo</h3>

              <div className="self-start">
                <SegmentedControl
                  options={[
                    { value: "tarjeta", label: "Tarjeta" },
                    { value: "pse", label: "PSE" },
                    { value: "nequi", label: "Nequi" },
                  ]}
                  value={medio}
                  onChange={(valor) => setMedio(valor as MedioRecarga)}
                />
              </div>
            </div>

            <form onSubmit={recargar} className="mt-4.5">
              <div className="mb-4.5 lg:max-w-175">
                <Field label="Monto a recargar (COP)" htmlFor="monto-recarga">
                  <Input
                    id="monto-recarga"
                    inputMode="numeric"
                    value={montoCop}
                    onChange={(event) => setMontoCop(event.target.value.replace(/\D/g, ""))}
                    required
                  />
                </Field>
              </div>

              <div className="lg:flex lg:items-start lg:gap-6">
              <div className="lg:min-h-[292px] lg:w-175 lg:flex-none">
              {medio === "tarjeta" && (
                <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] gap-5 lg:gap-6 items-center mb-4.5">
                  <TarjetaVisual
                    marca={detectarMarcaTarjeta(numero)}
                    numero={numero}
                    titular={titular}
                    mesExpiracion={mesExpiracion}
                    anioExpiracion={anioExpiracion}
                  />

                  <div className="md:max-w-sm">
                    <Field label="Número de tarjeta" htmlFor="recarga-card-number">
                      <Input
                        id="recarga-card-number"
                        inputMode="numeric"
                        autoComplete="cc-number"
                        value={numero}
                        onChange={(event) => setNumero(event.target.value)}
                        required
                      />
                    </Field>
                    <div className="grid grid-cols-3 gap-x-3">
                      <Field label="Mes (MM)" htmlFor="recarga-exp-month">
                        <Input
                          id="recarga-exp-month"
                          inputMode="numeric"
                          maxLength={2}
                          value={mesExpiracion}
                          onChange={(event) => setMesExpiracion(event.target.value)}
                          required
                        />
                      </Field>
                      <Field label="Año (AA)" htmlFor="recarga-exp-year">
                        <Input
                          id="recarga-exp-year"
                          inputMode="numeric"
                          maxLength={2}
                          value={anioExpiracion}
                          onChange={(event) => setAnioExpiracion(event.target.value)}
                          required
                        />
                      </Field>
                      <Field label="CVC" htmlFor="recarga-cvc">
                        <Input
                          id="recarga-cvc"
                          inputMode="numeric"
                          maxLength={4}
                          value={cvc}
                          onChange={(event) => setCvc(event.target.value)}
                          required
                        />
                      </Field>
                    </div>
                    <Field label="Nombre del titular" htmlFor="recarga-card-holder">
                      <Input
                        id="recarga-card-holder"
                        autoComplete="cc-name"
                        value={titular}
                        onChange={(event) => setTitular(event.target.value)}
                        required
                      />
                    </Field>
                  </div>
                </div>
              )}

              {medio === "pse" && (
                <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] gap-5 lg:gap-6 items-center mb-4.5">
                  <BancoVisual
                    bancoNombre={instituciones.find((i) => i.code === bancoCode)?.name}
                    montoCop={montoCop}
                  />

                  <div className="md:max-w-sm">
                    <Field label="Banco" htmlFor="recarga-banco">
                      <Select
                        id="recarga-banco"
                        value={bancoCode}
                        onChange={(event) => setBancoCode(event.target.value)}
                        options={instituciones.map((i) => ({ value: i.code, label: i.name }))}
                      />
                    </Field>
                    <div className="grid grid-cols-2 gap-x-3">
                      <Field label="Tipo de persona" htmlFor="recarga-tipo-persona">
                        <Select
                          id="recarga-tipo-persona"
                          value={tipoPersona}
                          onChange={(event) => setTipoPersona(event.target.value as "0" | "1")}
                          options={[
                            { value: "0", label: "Natural" },
                            { value: "1", label: "Jurídica" },
                          ]}
                        />
                      </Field>
                      <Field label="Tipo de documento" htmlFor="recarga-tipo-doc">
                        <Select
                          id="recarga-tipo-doc"
                          value={tipoDocumento}
                          onChange={(event) => setTipoDocumento(event.target.value)}
                          options={[
                            { value: "CC", label: "Cédula" },
                            { value: "NIT", label: "NIT" },
                          ]}
                        />
                      </Field>
                    </div>
                    <Field label="Número de documento" htmlFor="recarga-num-doc">
                      <Input
                        id="recarga-num-doc"
                        inputMode="numeric"
                        value={numeroDocumento}
                        onChange={(event) => setNumeroDocumento(event.target.value)}
                        required
                      />
                    </Field>
                    <p className="text-ink-3 text-xs flex items-center gap-1.5">
                      <Landmark className="size-3.5" aria-hidden />
                      Te llevaremos a la página de tu banco para autenticarte.
                    </p>
                  </div>
                </div>
              )}

              {medio === "nequi" && (
                <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] gap-5 lg:gap-6 items-center mb-4.5">
                  <NequiVisual telefono={telefonoNequi} montoCop={montoCop} />

                  <div className="md:max-w-sm">
                    <Field label="Celular registrado en Nequi" htmlFor="recarga-nequi-phone">
                      <Input
                        id="recarga-nequi-phone"
                        inputMode="numeric"
                        maxLength={10}
                        value={telefonoNequi}
                        onChange={(event) => setTelefonoNequi(event.target.value.replace(/\D/g, ""))}
                        required
                      />
                      <p className="text-ink-3 text-xs mt-1.5 flex items-center gap-1.5">
                        <Smartphone className="size-3.5" aria-hidden />
                        Recibirás una notificación en la app de Nequi para aceptar el pago.
                      </p>
                    </Field>
                  </div>
                </div>
              )}
              </div>

              <div className="mt-4.5 lg:mt-0 lg:flex-1">
                <SecureStrip />
              </div>
              </div>

              <div className="flex flex-col gap-3 mt-4.5 mb-4.5">
                <label className="flex items-center gap-2.5 text-sm text-ink-2 min-h-11">
                  <input
                    type="checkbox"
                    className="size-4.5 accent-brand"
                    checked={aceptaTerminos}
                    onChange={(event) => setAceptaTerminos(event.target.checked)}
                  />
                  <span>
                    Acepto los{" "}
                    {tokens && (
                      <a href={tokens.permalinkAceptacion} target="_blank" rel="noreferrer" className="text-brand underline">
                        términos y condiciones
                      </a>
                    )}
                    .
                  </span>
                </label>
                <label className="flex items-center gap-2.5 text-sm text-ink-2 min-h-11">
                  <input
                    type="checkbox"
                    className="size-4.5 accent-brand"
                    checked={aceptaDatos}
                    onChange={(event) => setAceptaDatos(event.target.checked)}
                  />
                  <span>
                    Autorizo el{" "}
                    {tokens && (
                      <a href={tokens.permalinkDatos} target="_blank" rel="noreferrer" className="text-brand underline">
                        tratamiento de mis datos personales
                      </a>
                    )}
                    .
                  </span>
                </label>
              </div>

              <div className="md:max-w-sm">
                {mensajeEspera && (
                  <div className="mb-4.5 flex items-center gap-2.5 text-sm text-ink-2">
                    <Spinner /> {mensajeEspera}
                  </div>
                )}
                {errorRecarga && (
                  <div className="mb-4.5">
                    <Alert variant="err" title="No se pudo recargar">
                      {errorRecarga}
                    </Alert>
                  </div>
                )}

                <Button
                  type="submit"
                  loading={recargando}
                  disabled={!formularioValido}
                  className="w-full justify-center"
                >
                  Recargar
                </Button>
              </div>
            </form>
          </div>

          {saldo && saldo.movimientos.length > 0 && (
            <div className="bg-surface border border-border rounded-md p-4.75">
              <h3 className="text-[15px] font-semibold mb-3.5">Movimientos recientes</h3>

              {/* Mobile: tarjetas, nunca la tabla con scroll horizontal (ver skill responsive-mobile-first). */}
              <div className="flex flex-col gap-3 md:hidden">
                {saldo.movimientos.map((movimiento) => (
                  <div key={movimiento.publicId} className="border border-border rounded-md p-3.5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold capitalize">{movimiento.medio ?? "--"}</span>
                      <Pill variant={ESTADO_PILL[movimiento.estado].variant}>
                        {ESTADO_PILL[movimiento.estado].label}
                      </Pill>
                    </div>
                    <div className="text-ink-2 text-sm">{formatCop(movimiento.montoCop)}</div>
                  </div>
                ))}
              </div>

              <div className="hidden md:block">
                <Table>
                  <thead>
                    <tr>
                      <TableHeadCell>Medio</TableHeadCell>
                      <TableHeadCell>Monto</TableHeadCell>
                      <TableHeadCell>Estado</TableHeadCell>
                    </tr>
                  </thead>
                  <tbody>
                    {saldo.movimientos.map((movimiento) => (
                      <tr key={movimiento.publicId}>
                        <TableCell className="capitalize">{movimiento.medio ?? "--"}</TableCell>
                        <TableCell>{formatCop(movimiento.montoCop)}</TableCell>
                        <TableCell>
                          <Pill variant={ESTADO_PILL[movimiento.estado].variant}>
                            {ESTADO_PILL[movimiento.estado].label}
                          </Pill>
                        </TableCell>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </div>
          )}
          </div>

          <div className="flex flex-col gap-4 lg:order-2">
            <div className="bg-ok-soft border border-[color-mix(in_srgb,var(--color-ok)_16%,transparent)] rounded-md p-4">
              <h3 className="text-xs font-semibold tracking-wide uppercase text-ok-ink flex items-center gap-1.5 mb-1.5">
                <Wallet className="size-4" aria-hidden />
                Saldo SMS / RCS
              </h3>
              <div className="text-[28px] font-semibold leading-none">
                {saldo ? formatCop(saldo.saldoCop) : "--"}{" "}
                <span className="text-sm font-normal text-ink-2">COP</span>
              </div>
              <p className="text-ink-2 text-sm mt-2">
                Solo paga envíos SMS y RCS que excedan tus incluidos. No paga WhatsApp ni tu
                suscripción.
              </p>
            </div>

            <div className="bg-surface border border-border rounded-md p-4">
              <h3 className="text-[15px] font-semibold mb-3">Formas de recargar saldo</h3>
              <div className="flex flex-col gap-3">
                <div className="flex items-start gap-2.5">
                  <CreditCard className="size-4.5 text-brand flex-none mt-0.5" aria-hidden />
                  <div>
                    <div className="font-semibold text-sm">Tarjeta</div>
                    <p className="text-ink-3 text-xs">Pago único en el widget de Wompi. No queda guardada.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5">
                  <Landmark className="size-4.5 text-brand flex-none mt-0.5" aria-hidden />
                  <div>
                    <div className="font-semibold text-sm">PSE</div>
                    <p className="text-ink-3 text-xs">Te lleva a la página de tu banco para autenticarte.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5">
                  <Smartphone className="size-4.5 text-brand flex-none mt-0.5" aria-hidden />
                  <div>
                    <div className="font-semibold text-sm">Nequi</div>
                    <p className="text-ink-3 text-xs">Aceptas el cobro con una notificación en tu app.</p>
                  </div>
                </div>
              </div>
              <p className="text-ink-3 text-xs mt-3.5 pt-3.5 border-t border-border">
                Estos tres son pagos de una sola vez. Si quieres que se cobre solo cada mes, agrega
                una tarjeta en{" "}
                <a href="/suscripcion" className="text-brand underline">
                  Suscripción
                </a>
                .
              </p>
            </div>

            <Alert variant="ok" title="Pulso no guarda tus datos de pago">
              El número de tarjeta se cifra en tu navegador y viaja directo a Wompi. PSE y Nequi
              se gestionan en la plataforma de tu banco o de tu app: Pulso solo guarda el estado
              y el monto del movimiento.
            </Alert>
          </div>
        </div>
      )}
    </AppShell>
  );
};
