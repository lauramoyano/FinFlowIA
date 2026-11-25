import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocalStorage } from "@/shared/hooks/useLocalStorage";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "finflowia-sidebar-collapsed";

interface SidebarContextValue {
  /** Desktop: icon-only vs. full-width sidebar. Persisted across visits. */
  isCollapsed: boolean;
  toggleCollapsed: () => void;
  /** Mobile: whether the sidebar drawer overlay is open. Not persisted. */
  isMobileOpen: boolean;
  openMobile: () => void;
  closeMobile: () => void;
}

const SidebarContext = createContext<SidebarContextValue | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useLocalStorage<boolean>(
    SIDEBAR_COLLAPSED_STORAGE_KEY,
    false,
  );
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const value = useMemo<SidebarContextValue>(
    () => ({
      isCollapsed,
      toggleCollapsed: () => setIsCollapsed((prev) => !prev),
      isMobileOpen,
      openMobile: () => setIsMobileOpen(true),
      closeMobile: () => setIsMobileOpen(false),
    }),
    [isCollapsed, setIsCollapsed, isMobileOpen],
  );

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}

export function useSidebar(): SidebarContextValue {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
