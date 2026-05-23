import { Outlet } from "react-router-dom";
import { Sidebar } from "@/shared/components/layout/Sidebar";
import { TopBar } from "@/shared/components/layout/TopBar";
import { ErrorBoundary } from "@/shared/components/ErrorBoundary";

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
