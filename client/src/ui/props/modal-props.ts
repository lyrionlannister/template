import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export type ModalIconVariant = "brand" | "danger" | "warn";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  icon?: LucideIcon;
  iconVariant?: ModalIconVariant;
  children?: ReactNode;
  footer?: ReactNode;
}
