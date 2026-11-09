import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";

export type Granularity = "day" | "month" | "year";

export interface CategoryBreakdown {
  category: string;
  transaction_type: "income" | "expense";
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

export interface TimeSeriesPoint {
  period: string;
  date: string;
  income: string;
  expense: string;
}

export interface DashboardChartsData {
  start_date: string;
  end_date: string;
  granularity: Granularity;
  time_series: TimeSeriesPoint[];
  by_category: CategoryBreakdown[];
}

export interface DashboardChartsParams {
  start_date: string;
  end_date: string;
  granularity: Granularity;
}

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get<ApiResponse<DashboardData>>("/dashboard");
    return response.data.data;
  },

  getDashboardCharts: async (params: DashboardChartsParams): Promise<DashboardChartsData> => {
    const response = await apiClient.get<ApiResponse<DashboardChartsData>>("/dashboard/charts", {
      params,
    });
    return response.data.data;
  },
};
