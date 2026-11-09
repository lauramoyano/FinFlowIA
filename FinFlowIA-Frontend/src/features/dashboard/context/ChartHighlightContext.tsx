import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

interface ChartHighlightContextValue {
  selectedCategory: string | null;
  toggleCategory: (category: string) => void;
  getOpacity: (category: string) => number;
}

const ChartHighlightContext = createContext<ChartHighlightContextValue | null>(null);

export function ChartHighlightProvider({ children }: { children: ReactNode }) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const toggleCategory = useCallback((category: string) => {
    setSelectedCategory((prev) => (prev === category ? null : category));
  }, []);

  const getOpacity = useCallback(
    (category: string) => (!selectedCategory || selectedCategory === category ? 1 : 0.3),
    [selectedCategory],
  );

  const value = useMemo(
    () => ({ selectedCategory, toggleCategory, getOpacity }),
    [selectedCategory, toggleCategory, getOpacity],
  );

  return (
    <ChartHighlightContext.Provider value={value}>{children}</ChartHighlightContext.Provider>
  );
}

export function useChartHighlight(): ChartHighlightContextValue {
  const ctx = useContext(ChartHighlightContext);
  if (!ctx) {
    throw new Error("useChartHighlight must be used within a ChartHighlightProvider");
  }
  return ctx;
}
