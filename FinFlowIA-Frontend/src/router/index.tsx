import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/shared/components/layout/AppLayout";
// NOTE: ProtectedRoute is intentionally NOT applied below yet.
// Per project decision, login/auth gating is being implemented last so the
// rest of the frontend can be built and navigated freely in the meantime.
// TODO(auth-final-phase): re-wrap the routes under `element: <ProtectedRoute />`
// (see git history / ProtectedRoute.tsx, which is fully implemented and ready)
// once login is the last remaining piece to wire up.
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { TransactionsPage } from "@/pages/TransactionsPage";
import { ReportsPage } from "@/pages/ReportsPage";

export const router = createBrowserRouter([
  // Public routes
  {
    path: "/",
    lazy: async () => {
      const { LandingPage } = await import("@/pages/LandingPage");
      return { Component: LandingPage };
    },
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    lazy: async () => {
      const { RegisterPage } = await import("@/pages/RegisterPage");
      return { Component: RegisterPage };
    },
  },

  // App routes (temporarily open — see TODO above re: ProtectedRoute)
  {
    element: <AppLayout />,
    children: [
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "transactions",
        element: <TransactionsPage />,
      },
      {
        path: "reports",
        element: <ReportsPage />,
      },
    ],
  },

  // Catch-all redirect
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
