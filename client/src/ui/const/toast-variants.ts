import { AlertTriangle, CheckCircle2, Info, XCircle, type LucideIcon } from "lucide-react";
import type { ToastVariant } from "../props/toast-props";

export const TOAST_VARIANT_ICON_CLASSES: Record<ToastVariant, string> = {
  ok: "bg-[rgba(37,201,158,.18)] text-[#25C99E]",
  err: "bg-[rgba(232,93,93,.18)] text-[#F2A3A3]",
  warn: "bg-[rgba(232,147,12,.2)] text-[#F2C14E]",
  info: "bg-[rgba(91,141,239,.2)] text-[#9DBEF7]",
};

export const TOAST_VARIANT_ICONS: Record<ToastVariant, LucideIcon> = {
  ok: CheckCircle2,
  err: XCircle,
  warn: AlertTriangle,
  info: Info,
};
