import { useAuthStore } from "@/features/auth/store/auth.store";
import { Button } from "@/shared/components/ui/Button";

export function TopBar() {
  const { user, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground">
          {/* Page title will be rendered by individual pages */}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium">{user.full_name}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
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
          <span className="ml-2">Logout</span>
        </Button>
      </div>
    </header>
  );
}
