import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useTransactions } from "@/features/transactions/hooks/useTransactions";
import { TransactionList } from "@/features/transactions/components/TransactionList";
import { TransactionForm } from "@/features/transactions/components/TransactionForm";
import { TransactionFiltersBar } from "@/features/transactions/components/TransactionFilters";
import { CategoryManager } from "@/features/categories/components/CategoryManager";
import { Button } from "@/shared/components/ui/Button";
import type { TransactionFilters } from "@/features/transactions/types/transaction.types";

export function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({ page: 1, page_size: 20 });
  const [showForm, setShowForm] = useState(false);
  const [showCategories, setShowCategories] = useState(false);
  const { t } = useTranslation("transactions");
  const { t: tCommon } = useTranslation("common");

  const { data, isLoading } = useTransactions(filters);

  const transactions = data?.data ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" data-testid="page-title">{t("page.title")}</h1>
          <p className="text-muted-foreground">{t("page.totalCount", { count: total })}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowCategories(!showCategories)}
            data-testid="manage-categories"
          >
            {showCategories ? tCommon("actions.close") : t("manager.manageButton")}
          </Button>
          <Button
            onClick={() => setShowForm(!showForm)}
            data-testid="add-transaction"
          >
            {showForm ? tCommon("actions.cancel") : t("page.addTransaction")}
          </Button>
        </div>
      </div>

      {showCategories && <CategoryManager />}

      {showForm && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">{t("page.newTransaction")}</h2>
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
            {t("page.pageOf", { page: data.page, totalPages: data.total_pages })}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!data.has_prev}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              {tCommon("actions.previous")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data.has_next}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              {tCommon("actions.next")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
