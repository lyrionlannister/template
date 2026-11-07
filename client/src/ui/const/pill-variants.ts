import type { PillVariant } from "../props/pill-props";

export const PILL_VARIANT_CLASSES: Record<PillVariant, string> = {
  wa: "bg-wa-soft text-wa-ink",
  sms: "bg-sms-soft text-sms-ink",
  rcs: "bg-rcs-soft text-rcs-ink",
  ok: "bg-ok-soft text-ok-ink",
  warn: "bg-warn-soft text-warn-ink",
  err: "bg-err-soft text-err-ink",
  info: "bg-info-soft text-info-ink",
  brand: "bg-brand-soft text-brand-ink",
  mint: "bg-accent-soft text-accent-ink",
  neutral: "bg-surface-2 text-ink-2",
};
