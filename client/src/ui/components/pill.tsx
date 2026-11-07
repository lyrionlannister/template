import type { FC } from "react";
import type { PillProps } from "../props/pill-props";
import { PILL_VARIANT_CLASSES } from "../const/pill-variants";
import { cn } from "../../shared/utils/cn";

export const Pill: FC<PillProps> = ({ variant, dot = true, children, className, ...rest }) => (
  <span
    className={cn(
      "inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full leading-normal",
      PILL_VARIANT_CLASSES[variant],
      className,
    )}
    {...rest}
  >
    {dot && <i className="w-1.5 h-1.5 rounded-full bg-current flex-none" aria-hidden />}
    {children}
  </span>
);
