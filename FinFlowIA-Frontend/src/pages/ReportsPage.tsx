import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ReportGenerator } from "@/features/reports/components/ReportGenerator";
import { ReportPreview } from "@/features/reports/components/ReportPreview";
import { useReport } from "@/features/reports/hooks/useReports";
import type { DateString } from "@/shared/types/common.types";

export function ReportsPage() {
  const [reportParams, setReportParams] = useState<{
    start_date: DateString;
    end_date: DateString;
  } | null>(null);
  const { t } = useTranslation("reports");

  const { data, isLoading } = useReport({
    start_date: reportParams?.start_date ?? "",
    end_date: reportParams?.end_date ?? "",
    enabled: !!reportParams,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("page.title")}</h1>
        <p className="text-muted-foreground">
          {t("page.subtitle")}
        </p>
      </div>

      <ReportGenerator onGenerate={setReportParams} />

      <ReportPreview report={data} isLoading={isLoading} />
    </div>
  );
}
