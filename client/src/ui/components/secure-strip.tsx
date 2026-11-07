import type { FC } from "react";
import { KeyRound, Lock, ShieldCheck } from "lucide-react";

export const SecureStrip: FC = () => (
  <div className="flex flex-col gap-2.5">
    <div className="flex items-start gap-2.5 bg-surface-2 border border-border rounded-md p-3">
      <Lock className="size-4 text-brand flex-none mt-0.5" aria-hidden />
      <div>
        <b className="block text-xs">Conexión protegida</b>
        <span className="text-ink-3 text-xs">Tus datos viajan protegidos hasta Wompi.</span>
      </div>
    </div>
    <div className="flex items-start gap-2.5 bg-surface-2 border border-border rounded-md p-3">
      <KeyRound className="size-4 text-brand flex-none mt-0.5" aria-hidden />
      <div>
        <b className="block text-xs">Tu tarjeta no se guarda</b>
        <span className="text-ink-3 text-xs">Wompi la cambia por un código que solo ellos pueden usar para cobrar.</span>
      </div>
    </div>
    <div className="flex items-start gap-2.5 bg-surface-2 border border-border rounded-md p-3">
      <ShieldCheck className="size-4 text-brand flex-none mt-0.5" aria-hidden />
      <div>
        <b className="block text-xs">Pulso nunca la ve completa</b>
        <span className="text-ink-3 text-xs">Ni el número completo ni el código de seguridad llegan a nosotros.</span>
      </div>
    </div>
  </div>
);
