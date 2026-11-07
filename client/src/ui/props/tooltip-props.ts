import type { ReactNode } from "react";

export interface TooltipProps {
  content: string;
  position?: "top" | "bottom";
  children: ReactNode;
}
