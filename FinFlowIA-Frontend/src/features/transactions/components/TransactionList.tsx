import { useMemo } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { CategoryBadge } from "@/features/transactions/components/CategoryBadge";
import { useDeleteTransaction } from "@/features/transactions/hooks/useCreateTransaction";
import { Button } from "@/shared/components/ui/Button";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";
import { cn, formatCurrency, formatDate } from "@/shared/lib/utils";
import type { Transaction } from "@/features/transactions/types/transaction.types";

const columnHelper = createColumnHelper<Transaction>();

function buildColumns(t: TFunction<"transactions">) {
  return [
    columnHelper.accessor("transaction_date", {
      header: t("list.columns.date"),
      cell: (info) => formatDate(info.getValue()),
    }),
    columnHelper.accessor("description", {
      header: t("list.columns.description"),
      cell: (info) => (
        <span className="font-medium">{info.getValue()}</span>
      ),
    }),
    columnHelper.accessor("category", {
      header: t("list.columns.category"),
      cell: (info) => <CategoryBadge category={info.getValue()} />,
    }),
    columnHelper.accessor("transaction_type", {
      header: t("list.columns.type"),
      cell: (info) => (
        <span
          data-transaction-type={info.getValue()}
          className={
            info.getValue() === "income"
              ? "text-green-700 dark:text-green-400 font-medium"
              : "text-red-600 dark:text-red-400 font-medium"
          }
        >
          {info.getValue() === "income" ? t("list.income") : t("list.expense")}
        </span>
      ),
    }),
    columnHelper.accessor("amount", {
      header: t("list.columns.amount"),
      cell: (info) => {
        const isIncome = info.row.original.transaction_type === "income";
        return (
          <span className={isIncome ? "text-green-700 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
            {isIncome ? "+" : "-"}
            {formatCurrency(info.getValue())}
          </span>
        );
      },
    }),
  ];
}

interface TransactionListProps {
  transactions: Transaction[];
  isLoading?: boolean;
}

export function TransactionList({ transactions, isLoading }: TransactionListProps) {
  const deleteMutation = useDeleteTransaction();
  const { t } = useTranslation("transactions");

  const allColumns = useMemo(() => {
    const base = buildColumns(t);
    return [
      ...base,
      columnHelper.display({
        id: "actions",
        header: t("list.columns.actions"),
        cell: (info) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteMutation.mutate(info.row.original.id)}
            disabled={deleteMutation.isPending}
            className="text-destructive hover:text-destructive"
            data-testid="delete-transaction-button"
          >
            {t("list.delete")}
          </Button>
        ),
      }),
    ];
  }, [t]);

  const table = useReactTable({
    data: transactions,
    columns: allColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div
        className="flex h-48 flex-col items-center justify-center text-muted-foreground"
        data-testid="transaction-list"
      >
        <p className="text-lg font-medium">{t("list.emptyTitle")}</p>
        <p className="text-sm">{t("list.emptySubtitle")}</p>
      </div>
    );
  }

  return (
    <div data-testid="transaction-list">
      {/* Card list below sm: a 6-column table doesn't fit a phone screen
          without horizontal scrolling or clipped cells (same problem the
          products table had) — a stacked card per transaction reads much
          better at that width. */}
      <div className="divide-y rounded-lg border sm:hidden">
        {transactions.map((tx) => {
          const isIncome = tx.transaction_type === "income";
          return (
            <div key={tx.id} className="flex flex-col gap-2 p-4" data-testid="transaction-row-mobile">
              <div className="flex items-start justify-between gap-2">
                <span className="min-w-0 truncate font-medium">{tx.description}</span>
                <span
                  className={cn(
                    "shrink-0 font-medium",
                    isIncome ? "text-green-700 dark:text-green-400" : "text-red-600 dark:text-red-400",
                  )}
                >
                  {isIncome ? "+" : "-"}
                  {formatCurrency(tx.amount)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
                  <span className="shrink-0">{formatDate(tx.transaction_date)}</span>
                  <CategoryBadge category={tx.category} />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => deleteMutation.mutate(tx.id)}
                  disabled={deleteMutation.isPending}
                  className="h-7 shrink-0 px-2 text-xs text-destructive hover:text-destructive"
                  data-testid="delete-transaction-button"
                >
                  {t("list.delete")}
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Full table from sm up. */}
      <div className="hidden overflow-x-auto rounded-lg border sm:block">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left font-medium text-muted-foreground"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b transition-colors hover:bg-muted/30"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
