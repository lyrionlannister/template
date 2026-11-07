import type { FC } from "react";
import type { FunnelRowProps } from "../props/funnel-row-props";

export const FunnelRow: FC<FunnelRowProps> = ({ label, percent, valueLabel }) => (
  <div className="grid grid-cols-[130px_1fr_90px] gap-3 items-center mb-3 text-sm">
    <span className="text-ink-2 truncate">{label}</span>
    <div className="h-6.5 rounded-[7px] bg-surface-3 overflow-hidden">
      <div
        className="h-full rounded-[7px] bg-brand transition-[width] duration-slower ease-out"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
    <span className="text-right font-bold font-display">{valueLabel}</span>
  </div>
);
