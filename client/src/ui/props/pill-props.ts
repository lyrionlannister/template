import type { HTMLAttributes, ReactNode } from "react";

export type PillVariant = "wa" | "sms" | "rcs" | "ok" | "warn" | "err" | "info" | "brand" | "mint" | "neutral";

export interface PillProps extends HTMLAttributes<HTMLSpanElement> {
  variant: PillVariant;
  dot?: boolean;
  children: ReactNode;
}
