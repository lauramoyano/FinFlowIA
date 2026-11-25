import type { TransactionType } from "@/features/transactions/types/transaction.types";
import type { UUID } from "@/shared/types/common.types";

export interface Category {
  id: UUID;
  name: string;
  transaction_type: TransactionType;
  icon: string | null;
  is_default: boolean;
}

export interface CreateCategoryRequest {
  name: string;
  transaction_type: TransactionType;
  icon?: string;
}
