import type { FC } from "react";
import type { ToolbarProps } from "../props/toolbar-props";

export const Toolbar: FC<ToolbarProps> = ({ children }) => (
  <div className="flex gap-2.5 items-center flex-wrap px-4 py-3.5 border-b border-border">{children}</div>
);
