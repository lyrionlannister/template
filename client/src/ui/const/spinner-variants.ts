import type { SpinnerSize, SpinnerVariant } from "../props/spinner-props";

export const SPINNER_VARIANT_CLASSES: Record<SpinnerVariant, string> = {
  brand: "border-[color-mix(in_srgb,var(--color-brand)_22%,transparent)] border-t-brand",
  mint: "border-[color-mix(in_srgb,var(--color-accent)_22%,transparent)] border-t-accent",
  neutral: "border-surface-3 border-t-ink-3",
};

export const SPINNER_SIZE_CLASSES: Record<SpinnerSize, string> = {
  sm: "w-4 h-4 border-2",
  md: "w-6.5 h-6.5 border-3",
  lg: "w-10 h-10 border-4",
};
