import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";

export interface CategoryBreakdown {
  category: string;
  total: string;
  count: number;
  percentage: number;
}

export interface DashboardData {
  total_income: string;
  total_expenses: string;
  balance: string;
  by_category: CategoryBreakdown[];
  recent_transactions: unknown[];
  period_label: string;
}

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get<ApiResponse<DashboardData>>("/dashboard");
    return response.data.data;
  },
};
