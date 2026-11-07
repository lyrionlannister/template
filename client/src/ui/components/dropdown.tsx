import { useEffect, useRef, useState, type FC } from "react";
import type { DropdownProps } from "../props/dropdown-props";
import { cn } from "../../shared/utils/cn";

export const Dropdown: FC<DropdownProps> = ({ trigger, items }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  return (
    <div className="relative inline-block" ref={ref}>
      <button type="button" onClick={() => setOpen((value) => !value)}>
        {trigger}
      </button>
      <div
        className={cn(
          "absolute top-[calc(100%+8px)] right-0 min-w-58 bg-surface border border-border rounded-2xl shadow-lg p-1.5 z-50 origin-top-right",
          "transition-[opacity,transform] duration-fast ease-out",
          open ? "opacity-100 visible translate-y-0 pointer-events-auto" : "opacity-0 invisible -translate-y-1.25 scale-98 pointer-events-none",
        )}
      >
        {items.map((item, index) => {
          if (item.kind === "separator") return <div key={index} className="h-px bg-border my-1.25 mx-1" />;
          if (item.kind === "header")
            return (
              <div key={index} className="px-2.75 pt-2.25 pb-1.75 text-[11px] font-bold tracking-[.08em] uppercase text-ink-3">
                {item.label}
              </div>
            );

          const Icon = item.icon;
          const Tag = item.href ? "a" : "button";
          return (
            <Tag
              key={index}
              type={item.href ? undefined : "button"}
              href={item.href}
              onClick={() => {
                item.onClick?.();
                setOpen(false);
              }}
              className={cn(
                "flex items-center gap-2.5 w-full box-border px-2.75 min-h-11 md:min-h-0 md:py-2.5 border-none bg-transparent rounded-sm text-[13.5px] font-medium text-ink text-left no-underline transition-colors duration-fast ease-out",
                "hover:bg-surface-2",
                item.danger && "text-err-ink",
              )}
            >
              {Icon && <Icon className="size-4" aria-hidden />}
              {item.label}
            </Tag>
          );
        })}
      </div>
    </div>
  );
};
