import type { FC } from "react";
import { Check } from "lucide-react";
import type { StepperProps } from "../props/stepper-props";
import { cn } from "../../shared/utils/cn";

export const Stepper: FC<StepperProps> = ({ steps, currentIndex }) => (
  <div className="flex gap-0 flex-wrap mb-5.5">
    {steps.map((step, index) => {
      const done = index < currentIndex;
      const on = index === currentIndex;
      return (
        <div key={step.label} className="flex items-center">
          <div
            className={cn(
              "flex items-center gap-2.25 px-3.5 py-2 pl-2 rounded-full font-semibold text-[13px] bg-none border-none",
              done ? "text-accent-ink" : on ? "text-brand-ink bg-brand-soft" : "text-ink-3",
            )}
          >
            <span
              className={cn(
                "w-6.5 h-6.5 rounded-full border grid place-items-center text-xs font-display",
                done ? "bg-accent-soft border-transparent text-accent-ink" : on ? "bg-brand border-brand text-white" : "bg-surface-3 border-border",
              )}
            >
              {done ? <Check className="size-3.5" aria-hidden /> : index + 1}
            </span>
            {step.label}
          </div>
          {index < steps.length - 1 && <span className="w-6.5 h-px bg-border-strong self-center" />}
        </div>
      );
    })}
  </div>
);
