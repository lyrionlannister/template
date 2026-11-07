import type { FC } from "react";
import type { SegmentedControlProps } from "../props/segmented-control-props";
import { cn } from "../../shared/utils/cn";

export const SegmentedControl: FC<SegmentedControlProps> = ({ options, value, onChange }) => (
  <div className="inline-flex bg-surface-3 rounded-[13px] p-1 gap-0.5">
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        aria-pressed={option.value === value}
        onClick={() => onChange(option.value)}
        className={cn(
          "border-none bg-transparent px-3.75 min-h-11 md:min-h-0 md:py-2 rounded-sm text-[13.5px] font-semibold text-ink-2 transition-colors duration-fast ease-out",
          option.value === value && "bg-surface text-ink shadow-sm",
        )}
      >
        {option.label}
      </button>
    ))}
  </div>
);
