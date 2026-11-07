import type { HTMLAttributes, ReactNode } from "react";

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  onRemove?: () => void;
}
