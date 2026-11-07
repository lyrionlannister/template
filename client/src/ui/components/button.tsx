import type { FC } from "react";
import { Loader2 } from "lucide-react";
import type { ButtonProps } from "../props/button-props";
import { BUTTON_SIZE_CLASSES, BUTTON_VARIANT_CLASSES } from "../const/button-variants";
import { cn } from "../../shared/utils/cn";

export const Button: FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className,
  children,
  ...rest
}) => (
  <button
    disabled={disabled || loading}
    aria-busy={loading}
    className={cn(
      "inline-flex items-center justify-center gap-2 font-semibold whitespace-nowrap",
      "transition-all duration-fast ease-out hover:-translate-y-px",
      "disabled:opacity-45 disabled:cursor-not-allowed disabled:pointer-events-none disabled:translate-y-0",
      BUTTON_VARIANT_CLASSES[variant],
      BUTTON_SIZE_CLASSES[size],
      className,
    )}
    {...rest}
  >
    {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
    {children}
  </button>
);
