import type { FC } from "react";
import { ArrowRight, Landmark } from "lucide-react";
import type { BancoVisualProps } from "../props/banco-visual-props";
import { formatCop } from "../../shared/utils/format-cop";

export const BancoVisual: FC<BancoVisualProps> = ({ bancoNombre, montoCop }) => (
  <div
    role="img"
    className="min-h-48 w-full max-w-86 mx-auto flex flex-col items-center justify-center text-center gap-3 rounded-2xl border border-dashed border-border bg-surface-2 p-6"
    aria-label={`Pago PSE${bancoNombre ? ` con ${bancoNombre}` : ""}`}
  >
    <span className="size-14 rounded-full bg-brand-soft text-brand-ink grid place-items-center">
      <Landmark className="size-6.5" aria-hidden />
    </span>
    <div>
      <div className="font-semibold text-[15px] text-ink">{bancoNombre || "Elige tu banco"}</div>
      <p className="text-ink-3 text-xs flex items-center justify-center gap-1 mt-1">
        Te llevamos a su página <ArrowRight className="size-3" aria-hidden />
      </p>
    </div>
    <div className="text-ink-3 text-xs">
      {montoCop ? formatCop(montoCop) : "--"} · vía Wompi
    </div>
  </div>
);
