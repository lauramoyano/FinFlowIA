import type { DateString, DateTimeString, UUID } from "@/shared/types/common.types";

export type TransactionType = "income" | "expense";

export type CategoryType =
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
