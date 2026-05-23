import { useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { useExportReport } from "@/features/reports/hooks/useReports";
import type { DateString } from "@/shared/types/common.types";

interface ReportGeneratorProps {
  onGenerate: (params: { start_date: DateString; end_date: DateString }) => void;
}

export function ReportGenerator({ onGenerate }: ReportGeneratorProps) {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const exportMutation = useExportReport();

  const handleGenerate = () => {
    if (startDate && endDate) {
      onGenerate({ start_date: startDate, end_date: endDate });
    }
  };

  const handleExport = (format: "csv" | "pdf") => {
    if (startDate && endDate) {
      exportMutation.mutate({ start_date: startDate, end_date: endDate, format });
    }
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <h2 className="mb-4 text-lg font-semibold">Generate Report</h2>
      <div className="flex flex-wrap gap-4">
        <Input
          label="Start Date"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="min-w-[160px]"
        />
        <Input
          label="End Date"
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="min-w-[160px]"
        />
        <div className="flex items-end gap-2">
          <Button onClick={handleGenerate} disabled={!startDate || !endDate}>
            Generate
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport("csv")}
            disabled={!startDate || !endDate || exportMutation.isPending}
          >
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport("pdf")}
            disabled={!startDate || !endDate || exportMutation.isPending}
          >
            Export PDF
          </Button>
        </div>
      </div>
    </div>
  );
}
