import { useMutation } from "@tanstack/react-query";
import { transactionsApi } from "@/features/transactions/api/transactions.api";

export function useParseTransactionText() {
  return useMutation({
    mutationFn: (text: string) => transactionsApi.parseText(text),
  });
}
