import type { FC } from "react";
import type { ConnectionCardProps } from "../props/connection-card-props";
import { cn } from "../../shared/utils/cn";

export const ConnectionCard: FC<ConnectionCardProps> = ({ label, description, status = "ok" }) => (
  <div className="bg-sidebar-2 border border-white/6 rounded-xl p-3">
    <div className="flex items-center gap-2 text-[12.5px] text-white font-semibold">
      <span
        className={cn(
          "w-2 h-2 rounded-full flex-none",
          status === "ok" ? "bg-accent shadow-[0_0_0_4px_rgba(37,201,158,.18)]" : "bg-err shadow-[0_0_0_4px_rgba(232,93,93,.18)]",
        )}
      />
      {label}
    </div>
    <p className="mt-1.5 text-[11.5px] text-sidebar-muted leading-[1.45]">{description}</p>
  </div>
);
