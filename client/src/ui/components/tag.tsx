import type { FC } from "react";
import { X } from "lucide-react";
import type { TagProps } from "../props/tag-props";
import { cn } from "../../shared/utils/cn";

export const Tag: FC<TagProps> = ({ children, onRemove, className, ...rest }) => (
  <span
    className={cn(
      "inline-flex items-center gap-1.5 text-[12.5px] font-medium px-2.75 py-1.25 rounded-full border border-border bg-surface-2 text-ink-2",
      className,
    )}
    {...rest}
  >
    {children}
    {onRemove && (
      <button
        type="button"
        onClick={onRemove}
        className="border-none bg-transparent text-ink-3 p-0 grid place-items-center hover:text-err transition-colors duration-fast ease-out"
        aria-label="Quitar"
      >
        <X className="size-3.5" aria-hidden />
      </button>
    )}
  </span>
);
