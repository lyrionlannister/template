import { useState, type FC } from "react";
import { ChevronDown } from "lucide-react";
import type { AccordionProps } from "../props/accordion-props";
import { cn } from "../../shared/utils/cn";

export const Accordion: FC<AccordionProps> = ({ items }) => {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="border border-border rounded-md overflow-hidden shadow-sm divide-y divide-border">
      {items.map((item) => {
        const open = item.id === openId;
        return (
          <div key={item.id}>
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setOpenId(open ? null : item.id)}
              className="w-full flex items-center gap-2.5 bg-surface border-none px-5 py-4.25 text-[14.5px] font-semibold text-ink text-left hover:bg-surface-2 transition-colors duration-fast ease-out"
            >
              {item.title}
              <ChevronDown
                className={cn("ml-auto text-ink-3 size-4.5 flex-none transition-transform duration-base", open && "rotate-180")}
                aria-hidden
              />
            </button>
            <div className={cn("grid transition-[grid-template-rows] duration-base ease-out", open ? "grid-rows-[1fr]" : "grid-rows-[0fr]")}>
              <div className="overflow-hidden">
                <div className="px-5 pb-4.5 text-ink-2 text-sm leading-[1.65]">{item.content}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
