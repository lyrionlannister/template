import type { ReactNode } from "react";

export type AlertVariant = "ok" | "warn" | "err" | "info";

export interface AlertProps {
  variant: AlertVariant;
  title: string;
  children?: ReactNode;
  onClose?: () => void;
}
