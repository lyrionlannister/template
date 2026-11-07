import type { FC } from "react";
import { ChevronDown } from "lucide-react";
import type { SelectProps } from "../props/select-props";
import { cn } from "../../shared/utils/cn";

export const Select: FC<SelectProps> = ({ options, invalid = false, className, ...rest }) => (
  <div className="relative">
    <select
      className={cn(
        "w-full box-border appearance-none bg-surface-2 border rounded-[13px] text-ink text-[14.5px] px-3.75 h-11.5 pr-10",
        "transition-colors duration-fast ease-out",
        "hover:border-border-strong",
        "focus:outline-none focus:bg-surface focus:border-brand focus:shadow-[0_0_0_4px_var(--color-brand-soft)]",
        invalid ? "border-err shadow-[0_0_0_4px_var(--color-err-soft)]" : "border-border",
        className,
      )}
      {...rest}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    <ChevronDown className="size-4 text-ink-3 absolute right-3.75 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden />
  </div>
);
