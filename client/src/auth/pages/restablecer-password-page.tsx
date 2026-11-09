import { useState, type FC, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import { ArrowRight, AudioWaveform } from "lucide-react";
import { useAuth } from "../hooks/use-auth";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";

export const RestablecerPasswordPage: FC = () => {
  const { restablecerPassword } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listo, setListo] = useState(false);

  const enviar = async (event: FormEvent) => {
    event.preventDefault();
    if (password !== confirmacion) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setEnviando(true);
    setError(null);
    try {
      await restablecerPassword(token, password);
      setListo(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo restablecer la contraseña.");
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

        {!token ? (
          <Alert variant="err" title="Enlace inválido">
            Este enlace no incluye un token de recuperación. Pide uno nuevo.
          </Alert>
        ) : listo ? (
          <Alert variant="ok" title="Contraseña actualizada">
            Ya puedes iniciar sesión con tu nueva contraseña.
          </Alert>
        ) : (
          <>
            <h1 className="text-[26px] mb-1.5">Elige una nueva contraseña</h1>
            <p className="text-ink-2 mb-6">Mínimo 8 caracteres, con letras y números.</p>
            <form onSubmit={enviar}>
              <Field label="Nueva contraseña" htmlFor="restablecer-pass">
                <Input
                  id="restablecer-pass"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </Field>
              <Field label="Confirma la contraseña" htmlFor="restablecer-pass-confirmacion">
                <Input
                  id="restablecer-pass-confirmacion"
                  type="password"
                  autoComplete="new-password"
                  value={confirmacion}
                  onChange={(event) => setConfirmacion(event.target.value)}
                  required
                />
              </Field>
              {error && (
                <div className="mb-4.5">
                  <Alert variant="err" title="No se pudo restablecer la contraseña">
                    {error}
                  </Alert>
                </div>
              )}
              <Button type="submit" loading={enviando} className="w-full justify-center">
                Guardar contraseña
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
