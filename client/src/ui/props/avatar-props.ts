import type { HTMLAttributes } from "react";

export type AvatarVariant = "brand" | "mint" | "sky" | "amber";

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  initials: string;
  variant?: AvatarVariant;
}
