import type { FC } from "react";
import type { SkeletonProps } from "../props/skeleton-props";
import { SKELETON_VARIANT_CLASSES } from "../const/skeleton-variants";
import { cn } from "../../shared/utils/cn";

export const Skeleton: FC<SkeletonProps> = ({ variant = "block", className, ...rest }) => (
  <div
    className={cn(
      "relative overflow-hidden bg-surface-2",
      "after:content-[''] after:absolute after:inset-0 after:bg-[linear-gradient(90deg,transparent,rgba(140,140,160,.14),transparent)] after:animate-[shim_1.6s_infinite]",
      SKELETON_VARIANT_CLASSES[variant],
      className,
    )}
    {...rest}
  />
);
