import type { FC } from "react";
import type { ProgressBarProps } from "../props/progress-bar-props";
import { cn } from "../../shared/utils/cn";

export const ProgressBar: FC<ProgressBarProps> = ({ value, className, ...rest }) => (
  <div className={cn("h-1.75 rounded-full bg-surface-3 overflow-hidden w-27.5", className)} {...rest}>
    <i className="block h-full rounded-full bg-accent-bright not-italic" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
  </div>
);
