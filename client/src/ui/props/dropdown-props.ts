import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export interface DropdownItemData {
  kind?: "item" | "separator" | "header";
  label?: string;
  icon?: LucideIcon;
  onClick?: () => void;
  href?: string;
  danger?: boolean;
}

export interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItemData[];
}
