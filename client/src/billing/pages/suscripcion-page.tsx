import { useCallback, useEffect, useRef, useState, type FC, type FormEvent } from "react";
import { CreditCard, RefreshCw, Settings } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { formatCop } from "../../shared/utils/format-cop";
import { formatFecha } from "../../shared/utils/format-fecha";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Pill } from "../../ui/components/pill";
import { Spinner } from "../../ui/components/spinner";
import { useBilling } from "../hooks/use-billing";
import { useWompiTokenizacion } from "../hooks/use-wompi-tokenizacion";
import type { TokensDeAceptacion } from "../types/fuente-de-pago";
import type { SuscripcionEstado } from "../types/suscripcion-estado";

const NAV_ITEMS = [{ label: "Ajustes", href: "/ajustes", icon: Settings }];

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

const INTERVALO_POLLING_MS = 2500;
const MAX_INTENTOS_POLLING = 40;

export const SuscripcionPage: FC = () => {
  const { obtenerSesionActual } = useAuth();
  const { obtenerTokensDeAceptacion, iniciarFuenteDePago, consultarEstadoFuenteDePago, obtenerEstadoSuscripcion } =
    useBilling();
  const { tokenizarTarjeta } = useWompiTokenizacion();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [suscripcion, setSuscripcion] = useState<SuscripcionEstado | null>(null);
  const [tokens, setTokens] = useState<TokensDeAceptacion | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const [numero, setNumero] = useState("");
  const [cvc, setCvc] = useState("");
  const [mesExpiracion, setMesExpiracion] = useState("");
  const [anioExpiracion, setAnioExpiracion] = useState("");
  const [titular, setTitular] = useState("");
  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [aceptaDatos, setAceptaDatos] = useState(false);

  const [cambiandoTarjeta, setCambiandoTarjeta] = useState(false);
  const [conectando, setConectando] = useState(false);
  const [errorConectar, setErrorConectar] = useState<string | null>(null);
  const [pasoActual, setPasoActual] = useState<"BROWSER_INFO" | "CHALLENGE" | null>(null);
  const [iframeHtml, setIframeHtml] = useState<string | null>(null);
  const poleando = useRef(false);

  const cargarTodo = useCallback(() => {
    setCargando(true);
    return Promise.all([obtenerSesionActual(), obtenerEstadoSuscripcion(), obtenerTokensDeAceptacion()])
      .then(([sesion, estadoActual, tokensDeAceptacion]) => {
        setUsuario(sesion);
        setSuscripcion(estadoActual);
        setTokens(tokensDeAceptacion);
      })
      .catch((err) =>
        setErrorCarga(err instanceof Error ? err.message : "No se pudo cargar la suscripción."),
      )
      .finally(() => setCargando(false));
  }, [obtenerSesionActual, obtenerEstadoSuscripcion, obtenerTokensDeAceptacion]);

  useEffect(() => {
    cargarTodo();
  }, [cargarTodo]);

  const pollearEstado = useCallback(
    async (publicId: string) => {
      poleando.current = true;
      for (let intento = 0; intento < MAX_INTENTOS_POLLING; intento += 1) {
        if (!poleando.current) return;
        const estado = await consultarEstadoFuenteDePago(publicId);

        if (estado.estado === "disponible") {
          setPasoActual(null);
          setIframeHtml(null);
          setConectando(false);
          setCambiandoTarjeta(false);
          await cargarTodo();
          return;
        }
        if (estado.estado === "fallida") {
          setPasoActual(null);
          setIframeHtml(null);
          setConectando(false);
          setErrorConectar("La tarjeta fue rechazada. Intenta con otra.");
          return;
        }

        setPasoActual(estado.pasoActual);
        setIframeHtml(estado.iframeHtml);
        await new Promise((resolve) => setTimeout(resolve, INTERVALO_POLLING_MS));
      }
      setConectando(false);
      setErrorConectar("La verificación tardó demasiado. Intenta de nuevo.");
    },
    [consultarEstadoFuenteDePago, cargarTodo],
  );

  const conectar = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) return;
    setConectando(true);
    setErrorConectar(null);
    try {
      const tarjeta = await tokenizarTarjeta({ numero, cvc, mesExpiracion, anioExpiracion, titular });
      const fuente = await iniciarFuenteDePago({
        token: tarjeta.token,
        acceptanceToken: tokens.acceptanceToken,
        acceptPersonalAuth: tokens.acceptPersonalAuth,
        marca: tarjeta.marca,
        ultimosCuatro: tarjeta.ultimosCuatro,
        mesExpiracion: tarjeta.mesExpiracion,
        anioExpiracion: tarjeta.anioExpiracion,
        titular: tarjeta.titular,
      });
      await pollearEstado(fuente.publicId);
    } catch (err) {
      setConectando(false);
      setErrorConectar(err instanceof Error ? err.message : "No se pudo conectar la tarjeta.");
    }
  };

  const formularioValido =
    numero.trim().length >= 13 &&
    cvc.trim().length >= 3 &&
    mesExpiracion.trim().length === 2 &&
    anioExpiracion.trim().length === 2 &&
    titular.trim().length > 0 &&
    aceptaTerminos &&
    aceptaDatos;

  const suscripcionActiva =
    suscripcion?.existe && (suscripcion.estado === "activa" || suscripcion.estado === "en_reintento");

  return (
    <AppShell
      navItems={NAV_ITEMS}
      activeHref="/ajustes"
      logoLabel="Pulso"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Suscripción</h1>
        <p className="text-ink-2 text-sm">Cobro mensual automático de tu plan.</p>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : errorCarga ? (
        <Alert variant="err" title="No se pudo cargar la suscripción">
          {errorCarga}
        </Alert>
      ) : suscripcionActiva && !cambiandoTarjeta ? (
        <div className="flex flex-col gap-5 max-w-xl">
          <div className="bg-surface border border-border rounded-md p-4.75">
            <h3 className="text-[15px] font-semibold mb-1 flex items-center gap-2">
              <RefreshCw className="size-4.5 text-brand" aria-hidden />
              Suscripción {suscripcion?.estado === "en_reintento" ? "con un pago pendiente" : "activa"}
            </h3>
            <div className="grid grid-cols-2 gap-x-4 gap-y-4 mt-4">
              <div>
                <span className="text-xs text-ink-3">Monto mensual</span>
                <div className="font-semibold">
                  {suscripcion?.montoCop ? formatCop(suscripcion.montoCop) : "--"}
                </div>
              </div>
              <div>
                <span className="text-xs text-ink-3">Próximo cobro</span>
                <div className="font-semibold">
                  {suscripcion?.proximaFechaCobro ? formatFecha(suscripcion.proximaFechaCobro) : "--"}
                </div>
              </div>
            </div>
            {suscripcion?.estado === "en_reintento" && (
              <div className="mt-4.5">
                <Alert variant="warn" title="Reintentando el cobro">
                  El último intento no se pudo procesar. Se reintentará automáticamente.
                </Alert>
              </div>
            )}
          </div>

          {suscripcion?.tarjeta && (
            <div className="bg-surface border border-border rounded-md p-4.75">
              <div className="flex items-start justify-between gap-3 mb-1">
                <h3 className="text-[15px] font-semibold flex items-center gap-2">
                  <CreditCard className="size-4.5 text-brand" aria-hidden />
                  Método de pago
                </h3>
                <Pill variant="ok">Cobro automático activo</Pill>
              </div>
              <p className="text-ink-2 text-sm mb-4.5">
                La tarjeta con la que se cobra tu suscripción cada mes. Queda{" "}
                <strong className="text-ink">tokenizada en Wompi</strong>: Pulso solo guarda la
                marca, los últimos 4 dígitos y el vencimiento — nunca el número completo ni el CVC.
              </p>

              <div
                className="rounded-xl p-5 text-white mb-4.5 bg-gradient-to-br from-brand to-brand-active"
                aria-label={`Tarjeta ${suscripcion.tarjeta.marca ?? ""} terminada en ${suscripcion.tarjeta.ultimosCuatro ?? "----"}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs tracking-wide opacity-80">PULSO</span>
                  <span className="text-sm font-semibold uppercase">
                    {suscripcion.tarjeta.marca ?? "Tarjeta"}
                  </span>
                </div>
                <div className="text-xl tracking-[0.2em] mt-6 mb-4">
                  •••• •••• •••• {suscripcion.tarjeta.ultimosCuatro ?? "----"}
                </div>
                <div className="flex items-end justify-between text-xs">
                  <span className="uppercase">{suscripcion.tarjeta.titular ?? "—"}</span>
                  <span>
                    {suscripcion.tarjeta.mesExpiracion ?? "--"}/{suscripcion.tarjeta.anioExpiracion ?? "--"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-x-4 gap-y-4 mb-4.5">
                <div>
                  <span className="text-xs text-ink-3">Marca</span>
                  <div className="font-semibold">{suscripcion.tarjeta.marca ?? "--"}</div>
                </div>
                <div>
                  <span className="text-xs text-ink-3">Terminación</span>
                  <div className="font-semibold">•••• {suscripcion.tarjeta.ultimosCuatro ?? "----"}</div>
                </div>
                <div>
                  <span className="text-xs text-ink-3">Titular</span>
                  <div className="font-semibold">{suscripcion.tarjeta.titular ?? "--"}</div>
                </div>
                <div>
                  <span className="text-xs text-ink-3">Vencimiento</span>
                  <div className="font-semibold">
                    {suscripcion.tarjeta.mesExpiracion ?? "--"} / {suscripcion.tarjeta.anioExpiracion ?? "--"}
                  </div>
                </div>
              </div>

              <p className="text-ink-2 text-sm mb-4.5">
                <span className="text-ink-3">Se usa para</span>
                <br />
                Suscripción mensual
                {suscripcion.proximaFechaCobro && (
                  <>
                    {" "}
                    · próximo cobro {formatFecha(suscripcion.proximaFechaCobro)}
                    {suscripcion.montoCop && ` · ${formatCop(suscripcion.montoCop)}`}
                  </>
                )}
              </p>

              <Button variant="secondary" onClick={() => setCambiandoTarjeta(true)}>
                Cambiar tarjeta
              </Button>

              <p className="text-ink-3 text-xs mt-4.5">
                <strong>Pulso no guarda tu tarjeta.</strong> Al agregarla, el número se cifra en tu
                navegador y viaja directo a Wompi, que lo tokeniza y puede pedir la verificación
                3-D Secure de tu banco. Aquí solo quedan la marca, los últimos 4 dígitos y el
                vencimiento.
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
          <h3 className="text-[15px] font-semibold mb-1 flex items-center gap-2">
            <CreditCard className="size-4.5 text-brand" aria-hidden />
            {cambiandoTarjeta ? "Cambiar tarjeta" : "Conectar tarjeta para la suscripción"}
          </h3>
          <p className="text-ink-2 text-sm mb-4.5">
            Tu banco puede pedir una verificación adicional la primera vez.
          </p>

          {iframeHtml && pasoActual === "BROWSER_INFO" && (
            <iframe srcDoc={iframeHtml} title="Verificación 3DS" style={{ display: "none" }} />
          )}

          {conectando && pasoActual === "CHALLENGE" && iframeHtml ? (
            <div>
              <p className="text-ink-2 text-sm mb-3">Completa la verificación de tu banco:</p>
              <iframe
                srcDoc={iframeHtml}
                title="Verificación 3DS"
                className="w-full border border-border rounded-md"
                style={{ height: "480px" }}
              />
            </div>
          ) : conectando ? (
            <div className="grid place-items-center py-10 gap-3">
              <Spinner />
              <p className="text-ink-2 text-sm">Verificando tu tarjeta…</p>
            </div>
          ) : (
            <form onSubmit={conectar}>
              <Field label="Número de tarjeta" htmlFor="sub-card-number">
                <Input
                  id="sub-card-number"
                  inputMode="numeric"
                  autoComplete="cc-number"
                  value={numero}
                  onChange={(event) => setNumero(event.target.value)}
                  required
                />
              </Field>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-x-4">
                <Field label="Mes (MM)" htmlFor="sub-card-exp-month">
                  <Input
                    id="sub-card-exp-month"
                    inputMode="numeric"
                    maxLength={2}
                    autoComplete="cc-exp-month"
                    value={mesExpiracion}
                    onChange={(event) => setMesExpiracion(event.target.value)}
                    required
                  />
                </Field>
                <Field label="Año (AA)" htmlFor="sub-card-exp-year">
                  <Input
                    id="sub-card-exp-year"
                    inputMode="numeric"
                    maxLength={2}
                    autoComplete="cc-exp-year"
                    value={anioExpiracion}
                    onChange={(event) => setAnioExpiracion(event.target.value)}
                    required
                  />
                </Field>
                <Field label="CVC" htmlFor="sub-card-cvc">
                  <Input
                    id="sub-card-cvc"
                    inputMode="numeric"
                    maxLength={4}
                    autoComplete="cc-csc"
                    value={cvc}
                    onChange={(event) => setCvc(event.target.value)}
                    required
                  />
                </Field>
              </div>

              <Field label="Nombre del titular" htmlFor="sub-card-holder">
                <Input
                  id="sub-card-holder"
                  autoComplete="cc-name"
                  value={titular}
                  onChange={(event) => setTitular(event.target.value)}
                  required
                />
              </Field>

              <label className="flex items-start gap-2.5 text-sm text-ink-2 mb-3 min-h-11">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4.5 accent-brand"
                  checked={aceptaTerminos}
                  onChange={(event) => setAceptaTerminos(event.target.checked)}
                />
                <span>
                  Acepto los{" "}
                  {tokens && (
                    <a
                      href={tokens.permalinkAceptacion}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand underline"
                    >
                      términos y condiciones
                    </a>
                  )}
                  .
                </span>
              </label>

              <label className="flex items-start gap-2.5 text-sm text-ink-2 mb-4.5 min-h-11">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4.5 accent-brand"
                  checked={aceptaDatos}
                  onChange={(event) => setAceptaDatos(event.target.checked)}
                />
                <span>
                  Autorizo el{" "}
                  {tokens && (
                    <a
                      href={tokens.permalinkDatos}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand underline"
                    >
                      tratamiento de mis datos personales
                    </a>
                  )}
                  .
                </span>
              </label>

              {errorConectar && (
                <div className="mb-4.5">
                  <Alert variant="err" title="No se pudo conectar la tarjeta">
                    {errorConectar}
                  </Alert>
                </div>
              )}

              <Button type="submit" disabled={!formularioValido} className="w-full justify-center">
                {cambiandoTarjeta ? "Guardar tarjeta nueva" : "Conectar tarjeta"}
              </Button>
              {cambiandoTarjeta && (
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full justify-center mt-2.5"
                  onClick={() => setCambiandoTarjeta(false)}
                >
                  Cancelar
                </Button>
              )}
            </form>
          )}
        </div>
      )}
    </AppShell>
  );
};
