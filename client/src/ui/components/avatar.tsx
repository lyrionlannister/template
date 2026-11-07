import type { FC } from "react";
import type { AvatarProps } from "../props/avatar-props";
import { AVATAR_VARIANT_CLASSES } from "../const/avatar-variants";
import { cn } from "../../shared/utils/cn";

export const Avatar: FC<AvatarProps> = ({ initials, variant = "brand", className, ...rest }) => (
  <div
    className={cn(
      "w-9 h-9 rounded-full flex-none grid place-items-center text-[12.5px] font-bold",
      AVATAR_VARIANT_CLASSES[variant],
      className,
    )}
    {...rest}
  >
    {initials}
  </div>
);
