import type { FC } from "react";
import type { RoutePillProps } from "../props/route-pill-props";

export const RoutePill: FC<RoutePillProps> = ({ children }) => (
  <span className="font-mono text-[11px] bg-surface-3 text-ink-2 border border-border px-2.25 py-0.75 rounded-full">
    {children}
  </span>
);
