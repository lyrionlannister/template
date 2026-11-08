import { useState, type FC, type FormEvent } from "react";
import { Link } from "react-router";
import { ArrowRight, AudioWaveform } from "lucide-react";
import { useAuth } from "../hooks/use-auth";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";

export const OlvidePasswordPage: FC = () => {
  const { solicitarRecuperacion } = useAuth();
  const [email, setEmail] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enviado, setEnviado] = useState(false);

  const enviar = async (event: FormEvent) => {
    event.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      await solicitarRecuperacion(email);
      setEnviado(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo enviar el correo.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg p-5">
      <div className="w-full max-w-100">
        <div className="flex items-center gap-2.75 mb-6">
          <div className="w-10 h-10 rounded-xl bg-brand grid place-items-center flex-none">
            <AudioWaveform className="size-5 text-white" aria-hidden />
          </div>
          <span className="font-display font-bold text-lg">Pulso</span>
        </div>

        {enviado ? (
          <Alert variant="ok" title="Revisa tu correo">
            Si existe una cuenta con ese correo, te enviamos un enlace para elegir una nueva contraseña. Vence en 30
            minutos.
          </Alert>
        ) : (
          <>
            <h1 className="text-[26px] mb-1.5">Recupera tu cuenta</h1>
            <p className="text-ink-2 mb-6">Te enviamos un enlace a tu correo para elegir una nueva contraseña.</p>
            <form onSubmit={enviar}>
              <Field label="Correo" htmlFor="olvide-email">
                <Input
                  id="olvide-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </Field>
              {error && (
                <div className="mb-4.5">
                  <Alert variant="err" title="No se pudo enviar el correo">
                    {error}
                  </Alert>
                </div>
              )}
              <Button type="submit" loading={enviando} className="w-full justify-center">
                Enviar enlace
                <ArrowRight className="size-4" aria-hidden />
              </Button>
            </form>
          </>
        )}

        <p className="text-center text-ink-2 text-[13.5px] mt-5.5">
          <Link to="/login" className="font-semibold text-ink">
            Volver a iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  );
};
