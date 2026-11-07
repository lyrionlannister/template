export type ConnectionCardStatus = "ok" | "err";

export interface ConnectionCardProps {
  label: string;
  description: string;
  status?: ConnectionCardStatus;
}
