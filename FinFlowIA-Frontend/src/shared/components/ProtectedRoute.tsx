import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { FullPageSpinner } from "@/shared/components/LoadingSpinner";

interface ProtectedRouteProps {
  redirectTo?: string;
}

/**
 * HOC that guards routes requiring authentication.
 * Redirects unauthenticated users to the login page.
 */
export function ProtectedRoute({ redirectTo = "/login" }: ProtectedRouteProps) {
  const { token, isLoading } = useAuthStore();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (!token) {
    return <Navigate to={redirectTo} replace />;
  }

  return <Outlet />;
}
