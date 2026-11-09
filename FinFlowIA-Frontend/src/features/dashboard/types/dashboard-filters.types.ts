import type { DateString } from "@/shared/types/common.types";
import type { Granularity } from "@/features/dashboard/api/dashboard.api";

export interface DashboardChartFilters {
  granularity: Granularity;
  start_date: DateString;
  end_date: DateString;
}
