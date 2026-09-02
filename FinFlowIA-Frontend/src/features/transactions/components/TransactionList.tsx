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
import { formatCurrency, formatDate } from "@/shared/lib/utils";
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
              ? "text-green-600 dark:text-green-400 font-medium"
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
          <span className={isIncome ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
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
    <div className="overflow-x-auto rounded-lg border" data-testid="transaction-list">
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
  );
}
