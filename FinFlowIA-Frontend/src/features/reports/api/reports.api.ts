import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";
import type { DateString } from "@/shared/types/common.types";

export interface CategorySummary {
  category: string;
  total: string;
  count: number;
  percentage: number;
}

export interface ReportData {
  report_type: string;
  start_date: DateString;
  end_date: DateString;
  total_income: string;
  total_expenses: string;
  net_balance: string;
  transaction_count: number;
  by_category: CategorySummary[];
  generated_at: string;
}

export const reportsApi = {
  getSummary: async (params: {
    start_date: DateString;
    end_date: DateString;
    report_type?: string;
  }): Promise<ReportData> => {
    const response = await apiClient.get<ApiResponse<ReportData>>("/reports/summary", {
      params,
    });
    return response.data.data;
  },

  exportReport: async (params: {
    start_date: DateString;
    end_date: DateString;
    format: "csv" | "pdf";
  }): Promise<Blob> => {
    const response = await apiClient.get("/reports/export", {
      params,
      responseType: "blob",
    });
    return response.data as Blob;
  },
};
