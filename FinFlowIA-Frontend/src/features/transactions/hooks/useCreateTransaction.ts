import { useMutation, useQueryClient } from "@tanstack/react-query";
import { transactionsApi } from "@/features/transactions/api/transactions.api";
import { TRANSACTIONS_QUERY_KEY } from "@/features/transactions/hooks/useTransactions";
import type { CreateTransactionRequest } from "@/features/transactions/types/transaction.types";

export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTransactionRequest) => transactionsApi.create(data),
    onSuccess: () => {
      // Invalidate and refetch all transaction queries
      void queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_QUERY_KEY] });
      // Also invalidate dashboard since totals may have changed
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof transactionsApi.update>[1] }) =>
      transactionsApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_QUERY_KEY] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => transactionsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_QUERY_KEY] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
