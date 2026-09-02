import type { DateString, DateTimeString, UUID } from "@/shared/types/common.types";

export type TransactionType = "income" | "expense";

/** The 11 system default categories (see backend enums.CategoryType). */
export type DefaultCategoryType =
  | "food"
  | "transport"
  | "utilities"
  | "supplies"
  | "marketing"
  | "payroll"
  | "rent"
  | "equipment"
  | "sales"
  | "services"
  | "other"
  | "uncategorized";

/**
 * A transaction's category can be one of the fixed defaults above OR any
 * custom category name a user created (see features/categories). The
 * `(string & {})` intersection keeps autocomplete/literal-checking for the
 * known defaults while still accepting arbitrary custom names — plain
 * `string` alone would work too, but would lose the editor autocomplete.
 */
export type CategoryType = DefaultCategoryType | (string & {});

export interface Transaction {
  id: UUID;
  user_id: UUID;
  description: string;
  amount: string; // Decimal as string from API
  transaction_type: TransactionType;
  category: CategoryType | null;
  ai_confidence: number | null;
  transaction_date: DateString;
  notes: string | null;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

export interface CreateTransactionRequest {
  description: string;
  amount: string;
  transaction_type: TransactionType;
  transaction_date: DateString;
  category?: CategoryType;
  notes?: string;
}

export interface UpdateTransactionRequest {
  description?: string;
  amount?: string;
  transaction_type?: TransactionType;
  transaction_date?: DateString;
  category?: CategoryType;
  notes?: string;
}

export interface TransactionFilters {
  transaction_type?: TransactionType;
  category?: CategoryType;
  start_date?: DateString;
  end_date?: DateString;
  page?: number;
  page_size?: number;
}
