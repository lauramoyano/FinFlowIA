import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { categoriesApi } from "@/features/categories/api/categories.api";
import type { CreateCategoryRequest } from "@/features/categories/types/category.types";
import type { TransactionType } from "@/features/transactions/types/transaction.types";
import type { UUID } from "@/shared/types/common.types";

export const CATEGORIES_QUERY_KEY = "categories";

/**
 * List categories visible to the current user: system defaults plus their
 * own custom ones. Pass a transactionType to filter by income/expense
 * (matches the backend's optional query param).
 */
export function useCategories(transactionType?: TransactionType) {
  return useQuery({
    queryKey: [CATEGORIES_QUERY_KEY, transactionType ?? "all"],
    queryFn: () => categoriesApi.list(transactionType),
    staleTime: 1000 * 60 * 5, // categories change rarely — 5 minutes
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCategoryRequest) => categoriesApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CATEGORIES_QUERY_KEY] });
    },
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => categoriesApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [CATEGORIES_QUERY_KEY] });
    },
  });
}
