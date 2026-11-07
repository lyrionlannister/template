import type { FC } from "react";
import { X } from "lucide-react";
import type { ToastProps } from "../props/toast-props";
import { TOAST_VARIANT_ICONS, TOAST_VARIANT_ICON_CLASSES } from "../const/toast-variants";

export const Toast: FC<ToastProps> = ({ variant, title, description, onClose }) => {
  const Icon = TOAST_VARIANT_ICONS[variant];

  return (
    <div className="relative flex gap-2.75 items-start bg-sidebar text-sidebar-ink rounded-2xl px-4 py-3.5 shadow-lg text-[13.5px] leading-normal animate-[toastIn_var(--duration-slow)_var(--ease-spring)]">
      <div className={`w-8 h-8 rounded-sm grid place-items-center flex-none mt-px ${TOAST_VARIANT_ICON_CLASSES[variant]}`}>
        <Icon className="size-4.5" aria-hidden />
      </div>
      <div className="flex-1 min-w-0">
        <b className="block text-sm">{title}</b>
        {description && <span className="text-sidebar-muted">{description}</span>}
      </div>
      <button
        type="button"
        onClick={onClose}
        className="border-none bg-transparent text-sidebar-muted min-w-11 min-h-11 md:min-w-0 md:min-h-0 md:p-0.5 grid place-items-center flex-none rounded-md hover:text-white transition-colors duration-fast ease-out"
        aria-label="Cerrar"
      >
        <X className="size-4" aria-hidden />
      </button>
    </div>
  );
};
