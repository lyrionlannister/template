export type ToastVariant = "ok" | "err" | "warn" | "info";

export interface ToastProps {
  variant: ToastVariant;
  title: string;
  description?: string;
  onClose: () => void;
}
