import type { HTMLAttributes } from "react";

export type SpinnerVariant = "brand" | "mint" | "neutral";
export type SpinnerSize = "sm" | "md" | "lg";

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SpinnerVariant;
  size?: SpinnerSize;
}
