import { useState, type FC, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { ArrowRight, AudioWaveform, CalendarClock, MessageCircle, Users } from "lucide-react";
import { OtpStep } from "../components/otp-step";
import { useAuth } from "../hooks/use-auth";
import { useGoogleIdentity } from "../hooks/use-google-identity";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";

const IconoGoogle: FC = () => (
  <svg className="size-4" viewBox="0 0 24 24" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.48a5.55 5.55 0 0 1-2.4 3.64v3.02h3.86c2.27-2.09 3.58-5.17 3.58-8.85Z"
    />
    <path
      fill="#34A853"
      d="M12 24c3.24 0 5.96-1.07 7.94-2.9l-3.86-3.02c-1.07.72-2.45 1.15-4.08 1.15-3.14 0-5.8-2.12-6.75-4.96H1.26v3.11A11.99 11.99 0 0 0 12 24Z"
    />
    <path fill="#FBBC05" d="M5.25 14.27a7.2 7.2 0 0 1 0-4.54V6.62H1.26a11.99 11.99 0 0 0 0 10.76l3.99-3.11Z" />
    <path
      fill="#EA4335"
      d="M12 4.77c1.77 0 3.35.61 4.6 1.8l3.42-3.42A11.9 11.9 0 0 0 12 0 11.99 11.99 0 0 0 1.26 6.62l3.99 3.11C6.2 6.89 8.86 4.77 12 4.77Z"
    />
  </svg>
);

export const SignInPage: FC = () => {
  const { login, loginConGoogle } = useAuth();
  const { iniciarSesionConGoogle } = useGoogleIdentity();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [enviandoGoogle, setEnviandoGoogle] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paso, setPaso] = useState<"formulario" | "otp">("formulario");

  const enviar = async (event: FormEvent) => {
    event.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      await login({ email, password });
      setPaso("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar sesión.");
    } finally {
      setEnviando(false);
    }
  };

  const continuarConGoogle = async () => {
    setEnviandoGoogle(true);
    setError(null);
    try {
      const idToken = await iniciarSesionConGoogle();
      await loginConGoogle(idToken);
      setPaso("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar sesión con Google.");
    } finally {
      setEnviandoGoogle(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-bg">
      <aside className="hidden md:flex md:w-2/5 lg:w-1/2 bg-sidebar text-sidebar-ink flex-col justify-end p-10 lg:p-14 relative overflow-hidden">
        <div className="flex items-center gap-2.75 mb-auto">
          <div className="w-10 h-10 rounded-xl bg-brand grid place-items-center flex-none">
            <AudioWaveform className="size-5 text-white" aria-hidden />
          </div>
          <span className="font-display font-bold text-lg">Pulso</span>
        </div>
        <h2 className="font-display text-[32px] leading-[1.15] mb-3 text-white max-w-md">
          Tus mensajes, en el momento exacto.
        </h2>
        <p className="text-sidebar-muted max-w-md mb-5.5">
          WhatsApp, SMS y RCS desde un solo lugar: carga tus contactos, crea audiencias y programa envíos que llegan
          solos.
        </p>
        <div className="flex gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.25 rounded-full bg-accent-bright/16 text-accent-bright">
            <MessageCircle className="size-3.5" aria-hidden />
            WhatsApp Business API
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.25 rounded-full bg-white/10 text-sidebar-ink">
            <Users className="size-3.5" aria-hidden />
            Audiencias dinámicas
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.25 rounded-full bg-white/10 text-sidebar-ink">
            <CalendarClock className="size-3.5" aria-hidden />
            Envíos programados
          </span>
        </div>
        <svg
          className="absolute left-0 bottom-0 w-full h-20 opacity-60"
          viewBox="0 0 600 80"
          fill="none"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path
            d="M0 40 H180 L205 40 220 12 245 68 262 40 H420 L438 40 450 22 466 58 478 40 H600"
            stroke="var(--color-accent-bright)"
            strokeWidth="2.5"
          />
        </svg>
      </aside>

      <div className="flex-1 flex items-center justify-center p-5 md:p-10">
        <div className="w-full max-w-100">
          {paso === "formulario" ? (
            <>
              <h1 className="text-[26px] mb-1.5">Inicia sesión</h1>
              <p className="text-ink-2 mb-6">Accede al panel de tu negocio.</p>
              <form onSubmit={enviar}>
                <Field label="Correo" htmlFor="login-email">
                  <Input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </Field>
                <Field label="Contraseña" htmlFor="login-pass">
                  <Input
                    id="login-pass"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </Field>
                <div className="flex justify-end mb-4.5">
                  <Link to="/olvide-password" className="text-[13px] font-semibold text-ink">
                    ¿Olvidaste tu contraseña?
                  </Link>
                </div>
                {error && (
                  <div className="mb-4.5">
                    <Alert variant="err" title="No se pudo iniciar sesión">
                      {error}
                    </Alert>
                  </div>
                )}
                <Button type="submit" loading={enviando} className="w-full justify-center">
                  Entrar a Pulso
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </form>
              <div className="flex items-center gap-3 my-5 text-ink-3 text-xs">
                <span className="flex-1 h-px bg-border" />o<span className="flex-1 h-px bg-border" />
              </div>
              <Button
                variant="ghost"
                loading={enviandoGoogle}
                onClick={continuarConGoogle}
                className="w-full justify-center"
              >
                <IconoGoogle />
                Continuar con Google
              </Button>
              <p className="text-center text-ink-2 text-[13.5px] mt-5.5">
                ¿Aún no tienes cuenta?{" "}
                <Link to="/registro" className="font-semibold text-ink">
                  Regístrate gratis
                </Link>
              </p>
            </>
          ) : (
            <OtpStep onVerified={() => navigate("/ajustes")} />
          )}
        </div>
      </div>
    </div>
  );
};
