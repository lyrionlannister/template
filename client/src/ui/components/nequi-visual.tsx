import type { FC } from "react";
import { BatteryFull, Smartphone, SignalHigh, Wifi } from "lucide-react";
import type { NequiVisualProps } from "../props/nequi-visual-props";
import { formatCop } from "../../shared/utils/format-cop";

export const NequiVisual: FC<NequiVisualProps> = ({ telefono, montoCop }) => (
  <div
    role="img"
    className="relative overflow-hidden rounded-2xl min-h-48 w-full max-w-86 mx-auto flex flex-col shadow-lg bg-[linear-gradient(130deg,color-mix(in_srgb,var(--color-brand)_78%,var(--color-sidebar))_0%,var(--color-sidebar)_58%,color-mix(in_srgb,var(--color-accent-bright)_30%,var(--color-sidebar))_135%)]"
    aria-label={`Notificación de Nequi${telefono ? ` en el celular ${telefono}` : ""}`}
  >
    <div className="flex items-center justify-between px-4 pt-2.5 text-white/85 text-[11px] font-semibold">
      <span>9:41</span>
      <span className="flex items-center gap-1">
        <SignalHigh className="size-3" aria-hidden />
        <Wifi className="size-3" aria-hidden />
        <BatteryFull className="size-3.5" aria-hidden />
      </span>
    </div>

    <div className="flex-1 flex items-center px-3 py-3">
      <div className="w-full rounded-2xl bg-white/95 backdrop-blur text-[#1a1a1a] shadow-md p-3 flex gap-2.5 items-start">
        <span className="size-9 rounded-xl bg-[#E6007E] text-white grid place-items-center flex-none">
          <Smartphone className="size-4.5" aria-hidden />
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-[13px]">Nequi</span>
            <span className="text-[11px] text-black/45">ahora</span>
          </div>
          <p className="text-[12px] leading-[1.4] mt-0.5">
            Pulso te solicita <b>{montoCop ? formatCop(montoCop) : "un pago"}</b>
            {telefono ? ` a ${telefono}` : ""}. Toca para aceptar.
          </p>
        </div>
      </div>
    </div>

    <p className="text-center text-[11px] text-white/70 pb-3">Así se ve en tu celular · vía Wompi</p>
  </div>
);
