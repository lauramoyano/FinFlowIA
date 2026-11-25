import { useQuery } from "@tanstack/react-query";
import { transactionsApi } from "@/features/transactions/api/transactions.api";
import type { TransactionFilters } from "@/features/transactions/types/transaction.types";

export const TRANSACTIONS_QUERY_KEY = "transactions";

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: [TRANSACTIONS_QUERY_KEY, filters],
    queryFn: () => transactionsApi.list(filters),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: [TRANSACTIONS_QUERY_KEY, id],
    queryFn: () => transactionsApi.getById(id),
    enabled: !!id,
  });
}
