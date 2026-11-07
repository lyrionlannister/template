import type { FC } from "react";
import type { TooltipProps } from "../props/tooltip-props";

export const Tooltip: FC<TooltipProps> = ({ content, position = "top", children }) => (
  <span className="has-tip inline-flex" data-tip={content} data-tip-pos={position === "bottom" ? "bottom" : undefined}>
    {children}
  </span>
);
