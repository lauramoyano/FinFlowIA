import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { productsApi } from "@/features/products/api/products.api";
import type { CreateProductRequest, UpdateProductRequest } from "@/features/products/types/product.types";
import type { UUID } from "@/shared/types/common.types";

export const PRODUCTS_QUERY_KEY = "products";

export function useProducts() {
  return useQuery({
    queryKey: [PRODUCTS_QUERY_KEY],
    queryFn: () => productsApi.list(),
    staleTime: 1000 * 60, // product costs change more often than categories
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProductRequest) => productsApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: UUID; data: UpdateProductRequest }) =>
      productsApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => productsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
    },
  });
}
