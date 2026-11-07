import type { FC } from "react";
import type { TarjetaVisualProps } from "../props/tarjeta-visual-props";

const agruparNumero = (numero: string): string => {
  const digitos = (numero ?? "").replace(/\D/g, "").slice(0, 16);
  const relleno = digitos.padEnd(16, "•");
  return (relleno.match(/.{1,4}/g) ?? []).join(" ");
};

const agruparConUltimosCuatro = (ultimosCuatro: string): string =>
  `•••• •••• •••• ${ultimosCuatro || "----"}`;

export const TarjetaVisual: FC<TarjetaVisualProps> = ({
  marca,
  numero = "",
  ultimosCuatro,
  titular = "",
  mesExpiracion = "",
  anioExpiracion = "",
}) => (
  <div
    className="rounded-xl p-5 text-white bg-gradient-to-br from-brand to-brand-active relative overflow-hidden"
    aria-label={`Tarjeta ${marca ?? ""} ${titular ? `de ${titular}` : ""}`.trim()}
  >
    <div
      className="absolute -right-10 -top-10 size-40 rounded-full bg-white/10"
      aria-hidden
    />
    <div className="relative flex items-start justify-between">
      <span className="text-2xl font-bold italic tracking-tight">
        {(marca ?? "TARJETA").toUpperCase()}
      </span>
      {ultimosCuatro !== undefined && (
        <span className="text-xs font-semibold bg-teal-400/90 text-teal-950 px-2.5 py-1 rounded-full">
          Predeterminada
        </span>
      )}
    </div>

    <div className="relative w-9 h-7 rounded-md bg-gradient-to-br from-amber-200 to-amber-400 mt-5 mb-5 grid grid-cols-3 grid-rows-2 gap-px p-[3px]">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="border border-amber-700/40 rounded-[1px]" />
      ))}
    </div>

    <div className="relative text-xl tracking-[0.2em] mb-5">
      {ultimosCuatro !== undefined ? agruparConUltimosCuatro(ultimosCuatro) : agruparNumero(numero)}
    </div>

    <div className="relative grid grid-cols-3 gap-2 text-xs">
      <div className="min-w-0">
        <div className="uppercase tracking-wide opacity-70 text-[10px] mb-0.5">Titular</div>
        <div className="font-semibold truncate">{titular || "—"}</div>
      </div>
      <div>
        <div className="uppercase tracking-wide opacity-70 text-[10px] mb-0.5">Vence</div>
        <div className="font-semibold">
          {mesExpiracion || "--"}/{anioExpiracion || "--"}
        </div>
      </div>
      <div>
        <div className="uppercase tracking-wide opacity-70 text-[10px] mb-0.5">Vía</div>
        <div className="font-semibold">Wompi</div>
      </div>
    </div>
  </div>
);
