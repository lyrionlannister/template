import { useState, type FC, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { ArrowRight, AudioWaveform } from "lucide-react";
import { OtpStep } from "../components/otp-step";
import { useAuth } from "../hooks/use-auth";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";

export const SignInPage: FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
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

  return (
    <div className="min-h-screen flex bg-bg">
      <aside className="hidden md:flex md:w-2/5 lg:w-1/2 bg-sidebar text-sidebar-ink flex-col justify-end p-10 lg:p-14">
        <div className="flex items-center gap-2.75 mb-auto">
          <div className="w-10 h-10 rounded-xl bg-brand grid place-items-center flex-none">
            <AudioWaveform className="size-5 text-white" aria-hidden />
          </div>
          <span className="font-display font-bold text-lg">Pulso</span>
        </div>
        <h2 className="font-display text-[32px] leading-[1.15] mb-3 text-white max-w-md">
          Tus mensajes, en el momento exacto.
        </h2>
        <p className="text-sidebar-muted max-w-md">
          WhatsApp, SMS y RCS desde un solo lugar: carga tus contactos, crea audiencias y programa envíos que llegan
          solos.
        </p>
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
