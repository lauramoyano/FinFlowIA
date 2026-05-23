import { useState } from "react";
import { useTransactions } from "@/features/transactions/hooks/useTransactions";
import { TransactionList } from "@/features/transactions/components/TransactionList";
import { TransactionForm } from "@/features/transactions/components/TransactionForm";
import { TransactionFiltersBar } from "@/features/transactions/components/TransactionFilters";
import { Button } from "@/shared/components/ui/Button";
import type { TransactionFilters } from "@/features/transactions/types/transaction.types";

export function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({ page: 1, page_size: 20 });
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading } = useTransactions(filters);

  const transactions = data?.data ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Transactions</h1>
          <p className="text-muted-foreground">{total} total transactions</p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          data-testid="add-transaction"
        >
          {showForm ? "Cancel" : "+ Add Transaction"}
        </Button>
      </div>

      {showForm && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">New Transaction</h2>
          <TransactionForm onSuccess={() => setShowForm(false)} />
        </div>
      )}

      <TransactionFiltersBar
        onFilter={(newFilters) => setFilters({ ...newFilters, page: 1, page_size: 20 })}
        onReset={() => setFilters({ page: 1, page_size: 20 })}
      />

      <TransactionList transactions={transactions} isLoading={isLoading} />

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {data.page} of {data.total_pages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!data.has_prev}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data.has_next}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
