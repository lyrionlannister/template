import type { LucideIcon } from "lucide-react";

export interface SelectableCardOption {
  value: string;
  label: string;
  description?: string;
  icon?: LucideIcon;
}

export interface SelectableCardGroupProps {
  options: SelectableCardOption[];
  value: string;
  onChange: (value: string) => void;
}
