import type { FC } from "react";
import type { TableCellProps } from "../props/table-props";
import { cn } from "../../shared/utils/cn";

export const TableCell: FC<TableCellProps> = ({ children, className, ...rest }) => (
  <td className={cn("px-4 py-3.75 border-b border-border/70 align-middle", className)} {...rest}>
    {children}
  </td>
);
