import { useForm } from "react-hook-form";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import type { TransactionFilters } from "@/features/transactions/types/transaction.types";

interface TransactionFiltersProps {
  onFilter: (filters: TransactionFilters) => void;
  onReset: () => void;
}

export function TransactionFiltersBar({ onFilter, onReset }: TransactionFiltersProps) {
  const { register, handleSubmit, reset } = useForm<TransactionFilters>();

  const onSubmit = (data: TransactionFilters) => {
    // Remove empty values
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v !== undefined),
    ) as TransactionFilters;
    onFilter(cleaned);
  };

  const handleReset = () => {
    reset();
    onReset();
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-wrap gap-3 rounded-lg border bg-card p-4"
    >
      <div className="min-w-[140px]">
        <label className="text-sm font-medium">Type</label>
        <select
          {...register("transaction_type")}
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>

      <div className="min-w-[140px]">
        <label className="text-sm font-medium">Category</label>
        <select
          {...register("category")}
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">All categories</option>
          <option value="food">Food</option>
          <option value="transport">Transport</option>
          <option value="utilities">Utilities</option>
          <option value="supplies">Supplies</option>
          <option value="marketing">Marketing</option>
          <option value="payroll">Payroll</option>
          <option value="rent">Rent</option>
          <option value="equipment">Equipment</option>
          <option value="sales">Sales</option>
          <option value="services">Services</option>
          <option value="other">Other</option>
        </select>
      </div>

      <Input
        label="From"
        type="date"
        className="min-w-[140px]"
        {...register("start_date")}
      />

      <Input
        label="To"
        type="date"
        className="min-w-[140px]"
        {...register("end_date")}
      />

      <div className="flex items-end gap-2">
        <Button type="submit" size="sm">
          Apply
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleReset}>
          Reset
        </Button>
      </div>
    </form>
  );
}
