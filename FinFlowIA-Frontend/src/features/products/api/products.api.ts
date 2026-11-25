import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";
import type {
  CreateProductRequest,
  Product,
  UpdateProductRequest,
} from "@/features/products/types/product.types";
import type { UUID } from "@/shared/types/common.types";

export const productsApi = {
  list: async (): Promise<Product[]> => {
    const response = await apiClient.get<ApiResponse<Product[]>>("/products");
    return response.data.data;
  },

  create: async (data: CreateProductRequest): Promise<Product> => {
    const response = await apiClient.post<ApiResponse<Product>>("/products", data);
    return response.data.data;
  },

  update: async (id: UUID, data: UpdateProductRequest): Promise<Product> => {
    const response = await apiClient.put<ApiResponse<Product>>(`/products/${id}`, data);
    return response.data.data;
  },

  delete: async (id: UUID): Promise<void> => {
    await apiClient.delete(`/products/${id}`);
  },
};
