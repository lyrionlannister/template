import type { ReactNode, TdHTMLAttributes, ThHTMLAttributes } from "react";

export interface TableProps {
  children: ReactNode;
}

export interface TableHeadCellProps extends ThHTMLAttributes<HTMLTableCellElement> {
  children: ReactNode;
}

export interface TableCellProps extends TdHTMLAttributes<HTMLTableCellElement> {
  children: ReactNode;
}
