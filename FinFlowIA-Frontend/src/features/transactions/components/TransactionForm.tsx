import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  createTransactionSchema,
  type CreateTransactionFormValues,
} from "@/features/transactions/schemas/transaction.schema";
import { useCreateTransaction } from "@/features/transactions/hooks/useCreateTransaction";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import type { Transaction } from "@/features/transactions/types/transaction.types";

interface TransactionFormProps {
  onSuccess?: (transaction: Transaction) => void;
  onCancel?: () => void;
}

export function TransactionForm({ onSuccess, onCancel }: TransactionFormProps) {
  const createMutation = useCreateTransaction();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateTransactionFormValues>({
    resolver: zodResolver(createTransactionSchema),
    defaultValues: {
      transaction_date: new Date().toISOString().split("T")[0],
      transaction_type: "expense",
    },
  });

  const onSubmit = (data: CreateTransactionFormValues) => {
    createMutation.mutate(data, {
      onSuccess: (transaction) => {
        reset();
        onSuccess?.(transaction);
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {createMutation.isError && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          Failed to create transaction. Please try again.
        </div>
      )}

      <Input
        label="Description"
        placeholder="e.g., Lunch with client"
        error={errors.description?.message}
        data-testid="description-input"
        {...register("description")}
      />

      <Input
        label="Amount"
        type="number"
        step="0.01"
        min="0.01"
        placeholder="0.00"
        error={errors.amount?.message}
        {...register("amount")}
      />

      <div>
        <label className="text-sm font-medium">Type</label>
        <select
          {...register("transaction_type")}
          name="type"
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
        {errors.transaction_type && (
          <p className="text-sm text-destructive">{errors.transaction_type.message}</p>
        )}
      </div>

      <Input
        label="Date"
        type="date"
        error={errors.transaction_date?.message}
        {...register("transaction_date")}
      />

      <div>
        <label className="text-sm font-medium">Category (optional — AI will suggest)</label>
        <select
          {...register("category")}
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">Let AI categorize</option>
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
        label="Notes (optional)"
        placeholder="Additional context..."
        error={errors.notes?.message}
        {...register("notes")}
      />

      <div className="flex gap-3 pt-2">
        <Button type="submit" isLoading={createMutation.isPending}>
          Add Transaction
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
