import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/shared/components/layout/AppLayout";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { HomePage } from "@/pages/HomePage";
import { DashboardPage } from "@/pages/DashboardPage";
import { TransactionsPage } from "@/pages/TransactionsPage";
import { ProductsPage } from "@/pages/ProductsPage";
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

  // App routes: require a session, otherwise redirect to /login
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "home", element: <HomePage /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "transactions", element: <TransactionsPage /> },
          { path: "products", element: <ProductsPage /> },
          { path: "reports", element: <ReportsPage /> },
        ],
      },
    ],
  },

  // Catch-all redirect
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
