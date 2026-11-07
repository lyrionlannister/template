import type { FC } from "react";
import type { TabsProps } from "../props/tabs-props";
import { cn } from "../../shared/utils/cn";

export const Tabs: FC<TabsProps> = ({ options, value, onChange }) => (
  <div role="tablist" className="flex gap-1 border-b border-border overflow-x-auto">
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        role="tab"
        aria-selected={option.value === value}
        onClick={() => onChange(option.value)}
        className={cn(
          "border-none bg-transparent px-3.75 min-h-11 md:min-h-0 md:py-2.75 text-sm font-semibold text-ink-2 border-b-2 border-transparent -mb-px whitespace-nowrap transition-colors duration-fast ease-out",
          "hover:text-ink",
          option.value === value && "text-brand-ink border-brand",
        )}
      >
        {option.label}
      </button>
    ))}
  </div>
);
