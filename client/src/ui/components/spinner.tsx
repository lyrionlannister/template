import type { FC } from "react";
import type { SpinnerProps } from "../props/spinner-props";
import { SPINNER_SIZE_CLASSES, SPINNER_VARIANT_CLASSES } from "../const/spinner-variants";
import { cn } from "../../shared/utils/cn";

export const Spinner: FC<SpinnerProps> = ({ variant = "brand", size = "md", className, ...rest }) => (
  <div
    role="status"
    aria-label="Cargando"
    className={cn(
      "rounded-full flex-none animate-[spin_.75s_linear_infinite]",
      SPINNER_VARIANT_CLASSES[variant],
      SPINNER_SIZE_CLASSES[size],
      className,
    )}
    {...rest}
  />
);
