import type { HTMLAttributes, ReactNode } from "react";
import { useInView } from "@/shared/hooks/useInView";
import { cn } from "@/shared/lib/utils";

interface RevealProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Stagger delay in ms — handy for animating a grid of cards in sequence. */
  delay?: number;
}

/**
 * Fades and slides its children into view the first time they scroll into
 * the viewport. A thin wrapper around useInView so individual sections don't
 * each re-implement the same observer + animation-class dance. Extends
 * HTMLAttributes so callers can pass role="listitem" etc. when the section
 * around it needs ARIA list semantics.
 */
export function Reveal({ children, className, delay = 0, style, ...props }: RevealProps) {
  const { ref, isInView } = useInView<HTMLDivElement>();

  return (
    <div
      ref={ref}
      style={{ ...(delay ? { animationDelay: `${delay}ms` } : undefined), ...style }}
      className={cn("opacity-0", isInView && "animate-fade-in-up", className)}
      {...props}
    >
      {children}
    </div>
  );
}
