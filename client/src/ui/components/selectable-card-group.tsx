import type { FC } from "react";
import type { SelectableCardGroupProps } from "../props/selectable-card-group-props";
import { cn } from "../../shared/utils/cn";

export const SelectableCardGroup: FC<SelectableCardGroupProps> = ({ options, value, onChange }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
    {options.map((option) => {
      const Icon = option.icon;
      const selected = option.value === value;
      return (
        <button
          key={option.value}
          type="button"
          aria-pressed={selected}
          onClick={() => onChange(option.value)}
          className={cn(
            "border-[1.5px] rounded-[12px] p-4 text-left bg-surface w-full transition-colors duration-fast ease-out",
            selected ? "border-brand bg-brand-soft" : "border-border hover:border-border-strong",
          )}
        >
          <div className="flex items-center gap-2 font-bold font-display text-[15px]">
            {Icon && <Icon className="size-4.25 text-brand" aria-hidden />}
            {option.label}
          </div>
          {option.description && <p className="mt-1.75 text-[12.5px] text-ink-2">{option.description}</p>}
        </button>
      );
    })}
  </div>
);
