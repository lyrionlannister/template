import { useState, type FC } from "react";
import { Link } from "react-router";
import {
  AudioWaveform,
  ChevronsUpDown,
  Filter,
  LogOut,
  Menu,
  Moon,
  PanelLeft,
  ReceiptText,
  Settings,
  Sun,
  Upload,
  Users,
  X,
} from "lucide-react";
import type { AppShellProps } from "../props/app-shell-props";
import { useTheme } from "../hooks/use-theme";
import { cn } from "../../shared/utils/cn";

// Mismo nav en toda la app (ver resources/Pulso Vistas del Sistema.html):
// solo las areas que ya existen construidas, nunca dashboard/campanas/
// plantillas todavia.
const NAV_GRUPOS = [
  {
    label: "Contactos",
    items: [
      { label: "Contactos", href: "/contactos", icon: Users },
      { label: "Importar", href: "/contactos/importar", icon: Upload },
    ],
  },
  {
    label: "Audiencias",
    items: [{ label: "Audiencias", href: "/audiencias", icon: Filter }],
  },
  {
    label: "Cuenta",
    items: [
      { label: "Facturación", href: "/suscripcion", icon: ReceiptText },
      { label: "Ajustes", href: "/ajustes", icon: Settings },
    ],
  },
];

export const AppShell: FC<AppShellProps> = ({
  activeHref,
  pageTitle,
  logoLabel,
  tenantNombre,
  planNombre,
  userName,
  userInitials,
  userRolLabel,
  onCerrarSesion,
  children,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [rail, setRail] = useState(false);
  const { tema, alternar } = useTheme();

  return (
    <div className="flex h-screen bg-bg overflow-hidden">
      {/* Scrim — solo existe como overlay en mobile (<768); en tablet+ el sidebar ya es visible y fijo */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-black/50 z-20 md:hidden" onClick={() => setMobileOpen(false)} aria-hidden />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 md:static md:z-auto",
          "bg-sidebar text-sidebar-ink flex flex-col transition-transform md:transition-[width] duration-base ease-out",
          "w-63", // mobile: cajón a ancho completo
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "md:w-19", // tablet: riel fijo, siempre visible, sin cajón
          rail ? "lg:w-19" : "lg:w-63", // laptop/desktop: completo por defecto, colapsable a mano
        )}
      >
        {/* h-16 (64px): debe coincidir siempre con el header de abajo (altura única de cabecera) */}
        <div className="h-16 min-h-16 box-border flex items-center gap-2.75 border-b border-sidebar-line px-4.5 md:px-0 md:justify-center lg:px-4.5 lg:justify-start">
          <div className="w-10 h-10 rounded-xl bg-brand flex-none grid place-items-center">
            <AudioWaveform className="size-5 text-white" aria-hidden />
          </div>
          <span className={cn("min-w-0 truncate", "md:hidden", rail ? "lg:hidden" : "lg:block")}>
            <span className="font-display font-bold text-[16.5px] block truncate">{logoLabel}</span>
            <small className="block text-[11.5px] text-sidebar-muted truncate">Panel del negocio</small>
          </span>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="ml-auto md:hidden w-11 h-11 -mr-2.5 grid place-items-center text-sidebar-muted hover:text-white"
            aria-label="Cerrar menú"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>

        {/* Workspace: tenant + plan. Hoy sin cambio de organizacion (un usuario pertenece a un solo tenant), es solo informativo. */}
        <div className="px-3 pt-3">
          <div
            className={cn(
              "w-full flex items-center gap-2.5 rounded-xl px-2.5 py-2 bg-sidebar-2",
              "md:justify-center lg:justify-start",
              !rail && "md:px-2.5",
            )}
          >
            <div className="w-8 h-8 rounded-full bg-brand text-white grid place-items-center text-xs font-bold flex-none">
              {tenantNombre.slice(0, 2).toUpperCase()}
            </div>
            <span className={cn("min-w-0 flex-1 text-left", "md:hidden", rail ? "lg:hidden" : "lg:block")}>
              <span className="block text-[13px] font-semibold truncate">{tenantNombre}</span>
              <span className="block text-[11.5px] text-sidebar-muted truncate">{planNombre}</span>
            </span>
            <ChevronsUpDown
              className={cn("size-4 text-sidebar-muted flex-none", "md:hidden", rail ? "lg:hidden" : "lg:block")}
              aria-hidden
            />
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-3.5">
          {NAV_GRUPOS.map((grupo) => (
            <div key={grupo.label} className="flex flex-col gap-1">
              <span
                className={cn(
                  "px-2.75 text-[11px] font-semibold uppercase tracking-wide text-sidebar-muted",
                  "md:hidden",
                  rail ? "lg:hidden" : "lg:block",
                )}
              >
                {grupo.label}
              </span>
              {grupo.items.map((item) => {
                const Icon = item.icon;
                const active = item.href === activeHref;
                const showLabel = (
                  <span className={cn("md:hidden", rail ? "lg:hidden" : "lg:inline")}>{item.label}</span>
                );
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex items-center gap-2.75 px-2.75 min-h-11 rounded-xl text-sm font-medium transition-colors duration-fast ease-out",
                      "md:justify-center",
                      !rail && "lg:justify-start",
                      active ? "bg-brand text-white" : "text-[#CFCCDF] hover:bg-sidebar-2 hover:text-white",
                    )}
                  >
                    <Icon className="size-4.5 flex-none" aria-hidden />
                    {showLabel}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="p-3.5 border-t border-sidebar-line flex items-center gap-2.5 md:justify-center lg:justify-start">
          <div className="w-9 h-9 rounded-full bg-brand text-white grid place-items-center text-xs font-bold flex-none">
            {userInitials}
          </div>
          <span className={cn("min-w-0 flex-1", "md:hidden", rail ? "lg:hidden" : "lg:block")}>
            <span className="block text-sm truncate">{userName}</span>
            <span className="block text-[11.5px] text-sidebar-muted truncate">{userRolLabel}</span>
          </span>
          <button
            type="button"
            onClick={onCerrarSesion}
            className={cn(
              "flex-none w-9 h-9 grid place-items-center rounded-lg text-sidebar-muted hover:text-white hover:bg-sidebar-2 transition-colors duration-fast ease-out",
              "md:hidden",
              rail ? "lg:grid" : "lg:grid",
            )}
            aria-label="Cerrar sesión"
          >
            <LogOut className="size-4.5" aria-hidden />
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {/* h-16 (64px): mismo valor que el header del sidebar de arriba, nunca independiente */}
        <header className="h-16 min-h-16 box-border bg-surface/90 border-b border-border flex items-center gap-3 px-5">
          {/* Mobile: abre el cajón. Solo existe <768, en tablet+ el sidebar ya está visible */}
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="md:hidden w-11 h-11 rounded-xl border border-border bg-surface text-ink-2 grid place-items-center hover:bg-surface-2 hover:text-ink transition-colors duration-fast ease-out"
            aria-label="Abrir menú"
          >
            <Menu className="size-4.5" aria-hidden />
          </button>
          {/* Laptop/desktop: colapsa a riel manualmente. No existe en mobile (cajón) ni tablet (riel fijo) */}
          <button
            type="button"
            onClick={() => setRail((value) => !value)}
            className="hidden lg:grid w-10 h-10 rounded-xl border border-border bg-surface text-ink-2 place-items-center hover:bg-surface-2 hover:text-ink transition-colors duration-fast ease-out"
            aria-label="Alternar barra lateral"
          >
            <PanelLeft className="size-4.5" aria-hidden />
          </button>

          <h1 className="text-[17px] font-semibold truncate">{pageTitle}</h1>
          <span className="hidden md:inline-flex items-center text-xs font-mono text-ink-3 bg-surface-2 border border-border rounded-full px-2.5 py-1">
            {activeHref}
          </span>

          <button
            type="button"
            onClick={alternar}
            className="ml-auto flex-none w-10 h-10 rounded-xl border border-border bg-surface text-ink-2 grid place-items-center hover:bg-surface-2 hover:text-ink transition-colors duration-fast ease-out"
            aria-label="Cambiar tema"
          >
            {tema === "dark" ? <Sun className="size-4.5" aria-hidden /> : <Moon className="size-4.5" aria-hidden />}
          </button>
        </header>
        <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
};
