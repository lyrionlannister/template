import { useEffect, useState, type FC, type FormEvent } from "react";
import { CreditCard, Settings } from "lucide-react";
import { useAuth } from "../../auth/hooks/use-auth";
import type { Usuario } from "../../auth/types/usuario";
import { formatCop } from "../../shared/utils/format-cop";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { Spinner } from "../../ui/components/spinner";
import { useBilling } from "../hooks/use-billing";
import { useWompiTokenizacion } from "../hooks/use-wompi-tokenizacion";
import type { Cobro } from "../types/cobro";
import type { OnboardingEstado } from "../types/onboarding-estado";

const NAV_ITEMS = [{ label: "Ajustes", href: "/ajustes", icon: Settings }];

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

export const OnboardingPage: FC = () => {
  const { obtenerSesionActual } = useAuth();
  const { obtenerEstadoOnboarding, pagarOnboarding } = useBilling();
  const { tokenizarTarjeta } = useWompiTokenizacion();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [estado, setEstado] = useState<OnboardingEstado | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const [numero, setNumero] = useState("");
  const [cvc, setCvc] = useState("");
  const [mesExpiracion, setMesExpiracion] = useState("");
  const [anioExpiracion, setAnioExpiracion] = useState("");
  const [titular, setTitular] = useState("");
  const [aceptaTerminos, setAceptaTerminos] = useState(false);
  const [aceptaDatos, setAceptaDatos] = useState(false);

  const [pagando, setPagando] = useState(false);
  const [errorPago, setErrorPago] = useState<string | null>(null);
  const [cobro, setCobro] = useState<Cobro | null>(null);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerEstadoOnboarding()])
      .then(([sesion, estadoActual]) => {
        setUsuario(sesion);
        setEstado(estadoActual);
      })
      .catch((err) =>
        setErrorCarga(err instanceof Error ? err.message : "No se pudo cargar el onboarding."),
      )
      .finally(() => setCargando(false));
  }, [obtenerSesionActual, obtenerEstadoOnboarding]);

  const pagar = async (event: FormEvent) => {
    event.preventDefault();
    if (!estado) return;
    setPagando(true);
    setErrorPago(null);
    try {
      const tarjeta = await tokenizarTarjeta({
        numero,
        cvc,
        mesExpiracion,
        anioExpiracion,
        titular,
      });
      const resultado = await pagarOnboarding({
        token: tarjeta.token,
        acceptanceToken: estado.acceptanceToken,
        acceptPersonalAuth: estado.acceptPersonalAuth,
      });
      setCobro(resultado);
    } catch (err) {
      setErrorPago(err instanceof Error ? err.message : "No se pudo procesar el pago.");
    } finally {
      setPagando(false);
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

  return (
    <AppShell
      navItems={NAV_ITEMS}
      activeHref="/ajustes"
      logoLabel="Pulso"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
    >
      <div className="mb-5">
        <h1 className="text-[22px] mb-1">Onboarding</h1>
        <p className="text-ink-2 text-sm">Pago único para activar tu organización en Pulso.</p>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : errorCarga ? (
        <Alert variant="err" title="No se pudo cargar el onboarding">
          {errorCarga}
        </Alert>
      ) : estado?.pagado || cobro ? (
        <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
          <Alert variant="ok" title="Onboarding pagado">
            {cobro
              ? "Tu pago quedó registrado. La confirmación final llega en unos segundos."
              : "Ya activaste tu organización en Pulso."}
          </Alert>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
          <h3 className="text-[15px] font-semibold mb-1 flex items-center gap-2">
            <CreditCard className="size-4.5 text-brand" aria-hidden />
            Pagar onboarding
          </h3>
          {estado && (
            <p className="text-ink-2 text-sm mb-4.5">
              Pago único de {formatCop(estado.precioCop)}, antes de IVA.
            </p>
          )}

          <form onSubmit={pagar}>
            <Field label="Número de tarjeta" htmlFor="card-number">
              <Input
                id="card-number"
                inputMode="numeric"
                autoComplete="cc-number"
                value={numero}
                onChange={(event) => setNumero(event.target.value)}
                required
              />
            </Field>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-x-4">
              <Field label="Mes (MM)" htmlFor="card-exp-month">
                <Input
                  id="card-exp-month"
                  inputMode="numeric"
                  maxLength={2}
                  autoComplete="cc-exp-month"
                  value={mesExpiracion}
                  onChange={(event) => setMesExpiracion(event.target.value)}
                  required
                />
              </Field>
              <Field label="Año (AA)" htmlFor="card-exp-year">
                <Input
                  id="card-exp-year"
                  inputMode="numeric"
                  maxLength={2}
                  autoComplete="cc-exp-year"
                  value={anioExpiracion}
                  onChange={(event) => setAnioExpiracion(event.target.value)}
                  required
                />
              </Field>
              <Field label="CVC" htmlFor="card-cvc">
                <Input
                  id="card-cvc"
                  inputMode="numeric"
                  maxLength={4}
                  autoComplete="cc-csc"
                  value={cvc}
                  onChange={(event) => setCvc(event.target.value)}
                  required
                />
              </Field>
            </div>

            <Field label="Nombre del titular" htmlFor="card-holder">
              <Input
                id="card-holder"
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
                {estado && (
                  <a
                    href={estado.permalinkAceptacion}
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
                {estado && (
                  <a
                    href={estado.permalinkDatos}
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

            {errorPago && (
              <div className="mb-4.5">
                <Alert variant="err" title="No se pudo procesar el pago">
                  {errorPago}
                </Alert>
              </div>
            )}

            <Button
              type="submit"
              loading={pagando}
              disabled={!formularioValido}
              className="w-full justify-center"
            >
              Pagar onboarding
            </Button>
          </form>
        </div>
      )}
    </AppShell>
  );
};
