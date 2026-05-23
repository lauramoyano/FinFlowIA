import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/shared/components/layout/AppLayout";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { ErrorBoundary } from "@/shared/components/ErrorBoundary";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { TransactionsPage } from "@/pages/TransactionsPage";
import { ReportsPage } from "@/pages/ReportsPage";

export const router = createBrowserRouter([
  // Public routes
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

  // Protected routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/dashboard" replace />,
          },
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
    ],
  },

  // Catch-all redirect
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
