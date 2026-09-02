import { Menu } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { Button } from "@/shared/components/ui/Button";
import { ThemeToggle } from "@/shared/components/ThemeToggle";
import { LanguageSwitcher } from "@/shared/components/LanguageSwitcher";
import { useSidebar } from "@/shared/providers/SidebarProvider";

export function TopBar() {
  const { user, logout } = useAuthStore();
  const { t } = useTranslation("common");
  const { openMobile } = useSidebar();

  return (
    <header className="flex h-16 items-center justify-between gap-2 border-b bg-card px-3 sm:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <button
          type="button"
          onClick={openMobile}
          className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground md:hidden"
          aria-label={t("openMenu")}
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="truncate text-lg font-semibold text-foreground">
          {/* Page title will be rendered by individual pages */}
        </h1>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <LanguageSwitcher />
        <ThemeToggle />

        {user && (
          <div className="ml-1 flex items-center gap-3 sm:ml-2">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{user.full_name}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={logout}
          className="text-muted-foreground hover:text-foreground"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
          <span className="ml-2 hidden sm:inline">{t("logout")}</span>
        </Button>
      </div>
    </header>
  );
}
