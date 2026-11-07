import { useState, type FC, type FormEvent } from "react";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../hooks/use-auth";
import type { OtpStepProps } from "../props/otp-step-props";
import type { CanalOtp } from "../types/canal-otp";
import { ApiError } from "../../shared/types/api-error";
import { Alert } from "../../ui/components/alert";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { SegmentedControl } from "../../ui/components/segmented-control";

const OPCIONES_CANAL = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "sms", label: "SMS" },
];

export const OtpStep: FC<OtpStepProps> = ({ onVerified }) => {
  const { enviarOtp, verificarOtp } = useAuth();
  const [canal, setCanal] = useState<CanalOtp>("whatsapp");
  const [codigo, setCodigo] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [verificando, setVerificando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const enviar = async () => {
    setEnviando(true);
    setError(null);
    try {
      await enviarOtp(canal);
      setEnviado(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo enviar el código.");
    } finally {
      setEnviando(false);
    }
  };

  const verificar = async (event: FormEvent) => {
    event.preventDefault();
    setVerificando(true);
    setError(null);
    try {
      await verificarOtp(codigo, canal);
      onVerified();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Código incorrecto.");
    } finally {
      setVerificando(false);
    }
  };

  return (
    <div>
      <h2 className="text-[22px] mb-1.5 flex items-center gap-2">
        <ShieldCheck className="size-5 text-brand" aria-hidden />
        Verifica tu acceso
      </h2>
      <p className="text-ink-2 text-sm mb-5">
        Por seguridad, cada inicio de sesión pide un código de un solo uso.
      </p>
      <Field label="Canal" htmlFor="otp-canal">
        <SegmentedControl
          options={OPCIONES_CANAL}
          value={canal}
          onChange={(value) => setCanal(value as CanalOtp)}
        />
      </Field>

      {!enviado ? (
        <Button type="button" onClick={enviar} loading={enviando} className="w-full justify-center mt-2">
          Enviar código
        </Button>
      ) : (
        <form onSubmit={verificar}>
          <Field label="Código de 6 dígitos" htmlFor="otp-codigo" hint="Revisa el canal que elegiste.">
            <Input
              id="otp-codigo"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={codigo}
              onChange={(event) => setCodigo(event.target.value.replace(/\D/g, ""))}
              autoFocus
            />
          </Field>
          <Button
            type="submit"
            loading={verificando}
            disabled={codigo.length !== 6}
            className="w-full justify-center mt-2"
          >
            Verificar
          </Button>
          <Button type="button" variant="ghost" onClick={enviar} loading={enviando} className="w-full justify-center mt-2">
            Reenviar código
          </Button>
        </form>
      )}

      {error && (
        <div className="mt-4">
          <Alert variant="err" title="Algo falló">
            {error}
          </Alert>
        </div>
      )}
    </div>
  );
};
