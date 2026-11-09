import type { ReactNode } from "react";

export interface AppShellProps {
  activeHref: string;
  pageTitle: string;
  logoLabel: string;
  tenantNombre: string;
  planNombre: string;
  userName: string;
  userInitials: string;
  userRolLabel: string;
  onCerrarSesion: () => void;
  children: ReactNode;
}
