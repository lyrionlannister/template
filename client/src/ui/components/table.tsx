import type { FC } from "react";
import type { TableProps } from "../props/table-props";

export const Table: FC<TableProps> = ({ children }) => (
  <div className="overflow-x-auto rounded-md">
    <table className="border-collapse w-full text-sm min-w-140">{children}</table>
  </div>
);
