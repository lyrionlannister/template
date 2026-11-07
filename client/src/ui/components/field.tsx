import type { FC } from "react";
import type { FieldProps } from "../props/field-props";

export const Field: FC<FieldProps> = ({ label, htmlFor, hint, error, children }) => (
  <div className="mb-4.5 last:mb-0">
    <label htmlFor={htmlFor} className="block text-[13.5px] font-semibold mb-1.75">
      {label}
    </label>
    {children}
    {error ? (
      <p className="text-[12.5px] text-err-ink mt-1.75 font-medium">{error}</p>
    ) : hint ? (
      <p className="text-[12.5px] text-ink-3 mt-1.75 leading-[1.55]">{hint}</p>
    ) : null}
  </div>
);
