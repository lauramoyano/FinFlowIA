import { useMutation, useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/features/reports/api/reports.api";
import type { DateString } from "@/shared/types/common.types";

export function useReport(params: {
  start_date: DateString;
  end_date: DateString;
  report_type?: string;
  enabled?: boolean;
}) {
  const { enabled = true, ...queryParams } = params;

  return useQuery({
    queryKey: ["reports", queryParams],
    queryFn: () => reportsApi.getSummary(queryParams),
    enabled: enabled && !!queryParams.start_date && !!queryParams.end_date,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useExportReport() {
  return useMutation({
    mutationFn: (params: {
      start_date: DateString;
      end_date: DateString;
      format: "csv" | "pdf";
      lang: "es" | "en";
    }) => reportsApi.exportReport(params),
    onSuccess: (blob, variables) => {
      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `report_${variables.start_date}_${variables.end_date}.${variables.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
  });
}
