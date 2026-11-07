import type { FC } from "react";
import type { TableHeadCellProps } from "../props/table-props";
import { cn } from "../../shared/utils/cn";

export const TableHeadCell: FC<TableHeadCellProps> = ({ children, className, ...rest }) => (
  <th
    className={cn(
      "text-left text-[11px] tracking-[.07em] uppercase text-ink-3 font-bold px-4 py-3 border-b border-border bg-surface-2",
      "first:rounded-tl-md last:rounded-tr-md",
      className,
    )}
    {...rest}
  >
    {children}
  </th>
);
