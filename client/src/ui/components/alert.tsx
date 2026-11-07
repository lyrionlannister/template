import type { FC } from "react";
import { X } from "lucide-react";
import type { AlertProps } from "../props/alert-props";
import { ALERT_VARIANT_CLASSES, ALERT_VARIANT_ICONS } from "../const/alert-variants";
import { cn } from "../../shared/utils/cn";

export const Alert: FC<AlertProps> = ({ variant, title, children, onClose }) => {
  const Icon = ALERT_VARIANT_ICONS[variant];

  return (
    <div
      className={cn(
        "flex gap-3 px-4.25 py-3.75 rounded-md text-sm items-start border leading-[1.55]",
        ALERT_VARIANT_CLASSES[variant],
      )}
    >
      <Icon className="size-4.5 flex-none mt-px" aria-hidden />
      <div className="flex-1 min-w-0">
        <b className="block mb-px">{title}</b>
        {children && <p className="opacity-85 text-[13.5px]">{children}</p>}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="ml-auto border-none bg-transparent text-inherit opacity-65 min-w-11 min-h-11 md:min-w-0 md:min-h-0 md:p-0.5 grid place-items-center flex-none rounded-md hover:opacity-100 transition-opacity duration-fast ease-out"
          aria-label="Cerrar"
        >
          <X className="size-4" aria-hidden />
        </button>
      )}
    </div>
  );
};
