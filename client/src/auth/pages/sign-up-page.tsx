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

export const SignUpPage: FC = () => {
  const { registrar } = useAuth();
  const navigate = useNavigate();
  const [nombreOrganizacion, setNombreOrganizacion] = useState("");
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
      await registrar({ nombreOrganizacion, email, password });
      setPaso("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la cuenta.");
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
          Empieza gratis, sin tarjeta.
        </h2>
        <p className="text-sidebar-muted max-w-md">
          14 días de prueba y 100 mensajes incluidos. Después, conecta tu WhatsApp Business y empieza a enviar.
        </p>
      </aside>

      <div className="flex-1 flex items-center justify-center p-5 md:p-10">
        <div className="w-full max-w-100">
          {paso === "formulario" ? (
            <>
              <h1 className="text-[26px] mb-1.5">Crea tu cuenta</h1>
              <p className="text-ink-2 mb-6">Tu negocio, tu equipo, tus envíos.</p>
              <form onSubmit={enviar}>
                <Field label="Nombre del negocio" htmlFor="registro-nombre">
                  <Input
                    id="registro-nombre"
                    autoComplete="organization"
                    value={nombreOrganizacion}
                    onChange={(event) => setNombreOrganizacion(event.target.value)}
                    required
                  />
                </Field>
                <Field label="Correo" htmlFor="registro-email">
                  <Input
                    id="registro-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </Field>
                <Field label="Contraseña" htmlFor="registro-pass" hint="Mínimo 8 caracteres, con letras y números.">
                  <Input
                    id="registro-pass"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </Field>
                {error && (
                  <div className="mb-4.5">
                    <Alert variant="err" title="No se pudo crear la cuenta">
                      {error}
                    </Alert>
                  </div>
                )}
                <Button type="submit" loading={enviando} className="w-full justify-center">
                  Crear cuenta
                  <ArrowRight className="size-4" aria-hidden />
                </Button>
              </form>
              <p className="text-center text-ink-2 text-[13.5px] mt-5.5">
                ¿Ya tienes cuenta?{" "}
                <Link to="/login" className="font-semibold text-ink">
                  Inicia sesión
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
