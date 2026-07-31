import { createContext, useContext, useId, useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface AccordionContextValue {
  openValue: string | null;
  toggle: (value: string) => void;
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

interface AccordionProps {
  children: ReactNode;
  className?: string;
  defaultValue?: string;
}

/** Single-open accordion. Hand-rolled (no Radix dep) but keeps the same a11y contract. */
export function Accordion({ children, className, defaultValue }: AccordionProps) {
  const [openValue, setOpenValue] = useState<string | null>(defaultValue ?? null);

  const toggle = (value: string) => {
    setOpenValue((current) => (current === value ? null : value));
  };

  return (
    <AccordionContext.Provider value={{ openValue, toggle }}>
      <div className={cn("divide-y divide-border", className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

interface AccordionItemProps {
  value: string;
  question: string;
  children: ReactNode;
}

export function AccordionItem({ value, question, children }: AccordionItemProps) {
  const ctx = useContext(AccordionContext);
  if (!ctx) {
    throw new Error("AccordionItem must be rendered inside an Accordion");
  }
  const { openValue, toggle } = ctx;
  const isOpen = openValue === value;
  const contentId = useId();
  const buttonId = useId();

  return (
    <div className="py-1">
      {/* h3 so each question participates in the page's heading outline for screen readers */}
      <h3>
        <button
          id={buttonId}
          type="button"
          aria-expanded={isOpen}
          aria-controls={contentId}
          onClick={() => toggle(value)}
          className="flex w-full items-center justify-between gap-4 rounded-md py-4 text-left text-base font-medium transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <span>{question}</span>
          <ChevronDown
            aria-hidden="true"
            className={cn(
              "h-5 w-5 shrink-0 text-muted-foreground transition-transform duration-200",
              isOpen && "rotate-180",
            )}
          />
        </button>
      </h3>
      <div
        id={contentId}
        role="region"
        aria-labelledby={buttonId}
        className={cn(
          "grid transition-all duration-200 ease-in-out",
          isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="overflow-hidden">
          <p className="pb-4 text-muted-foreground">{children}</p>
        </div>
      </div>
    </div>
  );
}
