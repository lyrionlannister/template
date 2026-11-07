import type { FC } from "react";
import type { ChartTooltipProps } from "../props/chart-tooltip-props";

export const ChartTooltip: FC<ChartTooltipProps> = ({ children, style }) => (
  <div
    className="absolute -translate-x-1/2 -translate-y-full bg-surface border border-border-strong rounded-[9px] shadow-lg px-2.5 py-1.75 text-xs leading-[1.45] whitespace-nowrap pointer-events-none z-6 text-ink"
    style={style}
  >
    {children}
  </div>
);
