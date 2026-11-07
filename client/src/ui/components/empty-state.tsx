import type { FC } from "react";
import type { EmptyStateProps } from "../props/empty-state-props";

export const EmptyState: FC<EmptyStateProps> = ({ icon: Icon, title, description, action }) => (
  <div className="border-[1.5px] border-dashed border-border-strong rounded-lg px-5.5 py-9.5 text-center bg-surface-2/55">
    <Icon className="size-8 text-ink-3 mx-auto" aria-hidden />
    <h4 className="text-base mt-3 mb-1.25">{title}</h4>
    {description && <p className="text-ink-2 text-[13.5px] max-w-95 mx-auto mb-4.5 leading-[1.6]">{description}</p>}
    {action}
  </div>
);
