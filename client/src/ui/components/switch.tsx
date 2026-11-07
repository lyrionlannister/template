import type { FC } from "react";
import type { SwitchProps } from "../props/switch-props";
import { cn } from "../../shared/utils/cn";

export const Switch: FC<SwitchProps> = ({ checked, onChange, label, disabled = false }) => (
  <button
    type="button"
    role="switch"
    aria-checked={checked}
    aria-label={label}
    disabled={disabled}
    onClick={() => onChange(!checked)}
    className={cn(
      // min-w/h-11 (44px) es el área táctil en mobile; el track visual (48x28) se centra dentro.
      // Desde md: el puntero ya no exige 44px, el botón vuelve a encoger al tamaño del track.
      "inline-flex items-center justify-center flex-none min-w-11 min-h-11 md:min-w-0 md:min-h-0",
      disabled && "opacity-45 cursor-not-allowed pointer-events-none",
    )}
  >
    <span
      className={cn(
        "relative w-12 h-7 rounded-full transition-colors duration-fast ease-out",
        checked ? "bg-brand" : "bg-surface-3",
      )}
    >
      <span
        className={cn(
          "absolute top-0.75 left-0.75 w-5.5 h-5.5 rounded-full bg-white shadow-[0_1px_3px_rgba(40,35,80,.22),0_3px_8px_rgba(40,35,80,.14)] transition-[left] duration-fast ease-out",
          checked && "left-5.75",
        )}
      />
    </span>
  </button>
);
