import { AlertTriangle, CheckCircle2, Info, XCircle, type LucideIcon } from "lucide-react";
import type { AlertVariant } from "../props/alert-props";

export const ALERT_VARIANT_CLASSES: Record<AlertVariant, string> = {
  ok: "bg-ok-soft text-ok-ink border-[color-mix(in_srgb,var(--color-ok)_16%,transparent)]",
  warn: "bg-warn-soft text-warn-ink border-[color-mix(in_srgb,var(--color-warn-bright)_22%,transparent)]",
  err: "bg-err-soft text-err-ink border-[color-mix(in_srgb,var(--color-err)_16%,transparent)]",
  info: "bg-info-soft text-info-ink border-[color-mix(in_srgb,var(--color-info)_16%,transparent)]",
};

export const ALERT_VARIANT_ICONS: Record<AlertVariant, LucideIcon> = {
  ok: CheckCircle2,
  warn: AlertTriangle,
  err: XCircle,
  info: Info,
};
