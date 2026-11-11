import type { FC } from "react";
import type { TextareaProps } from "../props/textarea-props";
import { cn } from "../../shared/utils/cn";
import { alInvalidoEnEspanol, limpiarValidezNativa } from "../../shared/utils/native-validation-message";

export const Textarea: FC<TextareaProps> = ({
  invalid = false,
  className,
  onInvalid,
  onChange,
  ...rest
}) => (
  <textarea
    className={cn(
      "w-full box-border bg-surface-2 border rounded-[13px] text-ink text-[14.5px] px-3.75 py-3 resize-y min-h-22 leading-[1.55]",
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
