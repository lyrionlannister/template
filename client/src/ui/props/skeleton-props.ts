import type { HTMLAttributes } from "react";

export type SkeletonVariant = "text" | "title" | "circle" | "block";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
}
