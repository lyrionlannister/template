import type { FC } from "react";
import type { StatCardProps } from "../props/stat-card-props";
import { cn } from "../../shared/utils/cn";

export const StatCard: FC<StatCardProps> = ({ label, value, delta, trend }) => (
  <div className="bg-surface border border-border rounded-md px-4.75 py-4.25 shadow-sm">
    <div className="text-xs text-ink-3 font-semibold tracking-[.02em]">{label}</div>
    <div className="font-display text-[26px] font-bold mt-0.75 tracking-[-.01em]">{value}</div>
    {delta && (
      <div className={cn("text-xs font-semibold", trend === "down" ? "text-err-ink" : "text-accent-ink")}>{delta}</div>
    )}
  </div>
);
