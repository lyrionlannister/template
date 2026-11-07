import type { ButtonSize, ButtonVariant } from "../props/button-props";

export const BUTTON_VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-brand text-white shadow-[0_6px_16px_-6px_color-mix(in_srgb,var(--color-brand)_60%,transparent)] hover:bg-brand-hover active:bg-brand-active",
  accent:
    "bg-accent-bright text-[#06382A] shadow-[0_6px_16px_-6px_color-mix(in_srgb,var(--color-accent-bright)_55%,transparent)] hover:brightness-[1.04]",
  secondary: "bg-surface border border-border-strong text-ink shadow-sm hover:bg-surface-2",
  ghost: "bg-transparent text-ink-2 hover:bg-surface-2 hover:text-ink",
  danger: "bg-err text-white hover:brightness-[.96]",
  "danger-ghost": "bg-err-soft text-err-ink",
};

export const BUTTON_SIZE_CLASSES: Record<ButtonSize, string> = {
  // h-11 (44px) en mobile por objetivo táctil (responsive-mobile-first); h-9 (36px, el de
  // template-design-system.html) desde md: en adelante, donde el puntero ya no exige 44px.
  // El prefijo md: es el breakpoint (768px); la clave `sm` de este objeto es el tamaño del botón, sin relación.
  sm: "h-11 md:h-9 px-3.5 text-[13px] rounded-[11px]",
  md: "h-11 px-4.75 text-sm rounded-[13px]",
  lg: "h-13 px-6.5 text-[15px] rounded-[15px]",
};
