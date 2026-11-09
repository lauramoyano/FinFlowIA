import type { UUID } from "@/shared/types/common.types";

export interface Product {
  id: UUID;
  name: string;
  unit_label: string | null;
  unit_insumos_cost: string; // Decimal as string from API
  unit_sale_price: string | null;
  is_active: boolean;
}

export interface CreateProductRequest {
  name: string;
  unit_label?: string;
  unit_insumos_cost: string;
  unit_sale_price: string;
}

export interface UpdateProductRequest {
  name?: string;
  unit_label?: string;
  unit_insumos_cost?: string;
  unit_sale_price?: string;
  is_active?: boolean;
}
