import type { FC } from "react";
import type { InputProps } from "../props/input-props";
import { cn } from "../../shared/utils/cn";
import { alInvalidoEnEspanol, limpiarValidezNativa } from "../../shared/utils/native-validation-message";

export const Input: FC<InputProps> = ({
  invalid = false,
  className,
  onInvalid,
  onChange,
  ...rest
}) => (
  <input
    className={cn(
      "w-full box-border bg-surface-2 border rounded-[13px] text-ink text-[14.5px] px-3.75 h-11.5",
      "transition-colors duration-fast ease-out placeholder:text-ink-3",
      "hover:border-border-strong",
      "focus:outline-none focus:bg-surface focus:border-brand focus:shadow-[0_0_0_4px_var(--color-brand-soft)]",
      invalid ? "border-err shadow-[0_0_0_4px_var(--color-err-soft)]" : "border-border",
      className,
    )}
    onInvalid={(event) => {
      alInvalidoEnEspanol(event);
      onInvalid?.(event);
    }}
    onChange={(event) => {
      limpiarValidezNativa(event);
      onChange?.(event);
    }}
    {...rest}
  />
);
