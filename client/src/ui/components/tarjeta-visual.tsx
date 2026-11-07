import type { FC } from "react";
import type { TarjetaVisualProps } from "../props/tarjeta-visual-props";

const agruparNumero = (numero: string): string => {
  const digitos = (numero ?? "").replace(/\D/g, "").slice(0, 16);
  const relleno = digitos.padEnd(16, "•");
  return (relleno.match(/.{1,4}/g) ?? []).join(" ");
};

const agruparConUltimosCuatro = (ultimosCuatro: string): string =>
  `•••• •••• •••• ${ultimosCuatro || "----"}`;

const Wordmark: FC<{ marca?: string | null }> = ({ marca }) =>
  marca === "Mastercard" ? (
    <span className="inline-flex items-center gap-1.5">
      <span className="inline-flex">
        <i className="size-6.25 rounded-full bg-[#EB001B] block" />
        <i className="size-6.25 rounded-full bg-[#F79E1B] block -ml-2.25 opacity-90" />
      </span>
      <span className="font-display font-semibold text-sm tracking-[0.01em] text-white">
        Mastercard
      </span>
    </span>
  ) : (
    <span className="font-display font-bold italic text-xl tracking-[0.13em] leading-none text-white">
      {(marca ?? "TARJETA").toUpperCase()}
    </span>
  );

export const TarjetaVisual: FC<TarjetaVisualProps> = ({
  marca,
  numero = "",
  ultimosCuatro,
  titular = "",
  mesExpiracion = "",
  anioExpiracion = "",
}) => (
  <div
    role="img"
    className="relative overflow-hidden rounded-2xl p-5 min-h-48 w-full max-w-86 mx-auto flex flex-col text-white shadow-lg bg-[linear-gradient(130deg,color-mix(in_srgb,var(--color-brand)_78%,var(--color-sidebar))_0%,var(--color-sidebar)_58%,color-mix(in_srgb,var(--color-accent-bright)_30%,var(--color-sidebar))_135%)]"
    aria-label={`Tarjeta ${marca ?? ""} ${titular ? `de ${titular}` : ""}`.trim()}
  >
    <div
      className="absolute -right-21 -bottom-26 size-52.5 rounded-full border border-white/15 pointer-events-none"
      aria-hidden
    />

    <div className="relative z-10 flex items-start gap-2">
      <Wordmark marca={marca} />
      {ultimosCuatro !== undefined && (
        <span className="ml-auto text-[10.5px] font-bold tracking-wide bg-accent-bright/20 text-[#6FE3C3] border border-accent-bright/40 px-2 py-0.75 rounded-full whitespace-nowrap">
          Predeterminada
        </span>
      )}
    </div>

    <svg
      width="36"
      height="27"
      viewBox="0 0 36 27"
      aria-hidden="true"
      className="relative z-10 mt-4"
    >
      <rect x="1" y="1" width="34" height="25" rx="5" fill="#E3C878" stroke="rgba(120,90,10,.45)" />
      <path
        d="M1 9.5h11M1 17.5h11M35 9.5H24M35 17.5H24M12 1v25M24 1v25"
        stroke="rgba(120,90,10,.45)"
        fill="none"
      />
    </svg>

    <div className="relative z-10 font-mono text-lg tracking-[0.09em] mt-auto mb-3.5 whitespace-nowrap">
      {ultimosCuatro !== undefined ? agruparConUltimosCuatro(ultimosCuatro) : agruparNumero(numero)}
    </div>

    <div className="relative z-10 flex gap-4.5">
      <span>
        <span className="block text-[9.5px] font-bold tracking-[0.14em] uppercase text-white/62 mb-0.5">
          Titular
        </span>
        <b className="text-[13px] tracking-[0.04em]">{titular || "—"}</b>
      </span>
      <span>
        <span className="block text-[9.5px] font-bold tracking-[0.14em] uppercase text-white/62 mb-0.5">
          Vence
        </span>
        <b className="text-[13px] tracking-[0.04em]">
          {mesExpiracion || "--"}/{anioExpiracion || "--"}
        </b>
      </span>
      <span className="ml-auto text-right">
        <span className="block text-[9.5px] font-bold tracking-[0.14em] uppercase text-white/62 mb-0.5">
          Vía
        </span>
        <b className="text-[13px] tracking-[0.04em]">Wompi</b>
      </span>
    </div>
  </div>
);
