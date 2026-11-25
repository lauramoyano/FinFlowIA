import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";
import type { Category, CreateCategoryRequest } from "@/features/categories/types/category.types";
import type { TransactionType } from "@/features/transactions/types/transaction.types";
import type { UUID } from "@/shared/types/common.types";

export const categoriesApi = {
  list: async (transactionType?: TransactionType): Promise<Category[]> => {
    const params = transactionType ? `?transaction_type=${transactionType}` : "";
    const response = await apiClient.get<ApiResponse<Category[]>>(`/categories${params}`);
    return response.data.data;
  },

  create: async (data: CreateCategoryRequest): Promise<Category> => {
    const response = await apiClient.post<ApiResponse<Category>>("/categories", data);
    return response.data.data;
  },

  delete: async (id: UUID): Promise<void> => {
    await apiClient.delete(`/categories/${id}`);
  },
};
