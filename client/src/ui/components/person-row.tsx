import type { FC } from "react";
import type { PersonRowProps } from "../props/person-row-props";
import { Avatar } from "./avatar";

export const PersonRow: FC<PersonRowProps> = ({ name, subtitle, initials }) => (
  <div className="flex items-center gap-2.75 min-w-0">
    <Avatar initials={initials} />
    <div className="min-w-0">
      <b className="block text-[13px] font-semibold text-ink truncate">{name}</b>
      {subtitle && <span className="block text-xs text-ink-3 truncate">{subtitle}</span>}
    </div>
  </div>
);
