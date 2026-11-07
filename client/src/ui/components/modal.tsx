import type { FC } from "react";
import type { ModalProps } from "../props/modal-props";
import { MODAL_ICON_VARIANT_CLASSES } from "../const/modal-icon-variants";

export const Modal: FC<ModalProps> = ({ open, onClose, title, description, icon: Icon, iconVariant = "brand", children, footer }) => {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-[rgba(24,22,38,.48)] backdrop-blur-[3px] grid place-items-center z-110 p-4.5"
      onClick={onClose}
    >
      <div
        className="bg-surface rounded-xl max-w-112.5 w-full p-7.5 shadow-lg animate-[modalIn_var(--duration-slow)_var(--ease-spring)]"
        onClick={(event) => event.stopPropagation()}
      >
        {Icon && (
          <div className={`w-12 h-12 rounded-md grid place-items-center mb-4 ${MODAL_ICON_VARIANT_CLASSES[iconVariant]}`}>
            <Icon className="size-6" aria-hidden />
          </div>
        )}
        <h3 className="text-xl mb-2.25">{title}</h3>
        {description && <p className="text-ink-2 text-[14.5px] leading-[1.6]">{description}</p>}
        {children}
        {footer && <div className="flex gap-2.5 justify-end mt-6 flex-wrap">{footer}</div>}
      </div>
    </div>
  );
};
