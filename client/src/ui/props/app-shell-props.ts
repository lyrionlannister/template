import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export interface AppShellNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface AppShellProps {
  navItems: AppShellNavItem[];
  activeHref: string;
  logoLabel: string;
  userName: string;
  userInitials: string;
  children: ReactNode;
}
