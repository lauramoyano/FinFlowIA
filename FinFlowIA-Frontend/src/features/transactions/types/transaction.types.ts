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

/**
 * Result of POST /transactions/parse — a chat message interpreted into
 * transaction fields, NOT YET created. When `error` is set the other fields
 * are not reliable and must not be used to create a transaction.
 */
export interface ParsedTransaction {
  description: string;
  amount: string | null;
  transaction_type: TransactionType | null;
  transaction_date: DateString;
  category: CategoryType;
  confidence: number;
  error: string | null;
}

export interface TransactionFilters {
  transaction_type?: TransactionType;
  category?: CategoryType;
  start_date?: DateString;
  end_date?: DateString;
  page?: number;
  page_size?: number;
}

/**
 * Name of a recognized-but-unbuilt agent. All 4 current agents are
 * implemented — this type exists for forward-compatibility with a future
 * 5th agent the orchestrator might route to before it's built.
 */
export type UnavailableAgent = string;

/** One resolved line item within a completed production cost estimate. */
export interface ProductionEstimateItem {
  product_name: string;
  quantity: number;
  unit_cost: string; // Decimal as string from API
  subtotal: string;
}

/** Result of a completed production cost estimate (every item matched to a catalog cost). */
export interface ProductionEstimate {
  items: ProductionEstimateItem[];
  total_estimated_cost: string;
  // Present only when every item has a known sale price.
  projected_revenue: string | null;
  estimated_profit: string | null;
}

/** Result of a completed sales-goal estimate (minimum units to sell to hit a revenue target). */
export interface SalesGoalItem {
  product_name: string;
  quantity_needed: number;
  unit_sale_price: string;
  unit_insumos_cost: string;
  insumos_investment: string;
  projected_revenue: string;
  estimated_profit: string;
}

export interface SalesGoalResult {
  goal_amount: string;
  items: SalesGoalItem[]; // several products split the goal evenly
  insumos_investment: string;
  projected_revenue: string;
  estimated_profit: string;
}

/** One line item of a completed reparto (financial recommendation) result. */
export interface FinancialRecommendationItem {
  label: string;
  amount: string; // Decimal as string from API
  percentage: string;
}

/** Result of a completed financial-recommendation estimate (how to split a sale's net amount). */
export interface FinancialRecommendationResult {
  items: FinancialRecommendationItem[];
  sale_amount: string;
  total_costs: string;
  net_amount: string;
  estimated_savings: string;
  estimated_business_balance: string;
  pending_debt_total: string;
  // Set when insumos were recalled from a previous estimate.
  insumos_linked_products: string[] | null;
}

/** Income/expense/balance totals for one resolved date range. */
export interface PeriodSummaryData {
  label: string;
  start_date: DateString;
  end_date: DateString;
  total_income: string; // Decimal as string from API
  total_expenses: string;
  balance: string;
}

/** Result of a completed period-summary request (plus a comparison period, if requested). */
export interface PeriodSummaryResult {
  current: PeriodSummaryData;
  previous: PeriodSummaryData | null;
}

/**
 * Result of POST /orchestrator/message — one turn of the multi-agent chat.
 * `conversation_id` must be sent back on the next message to continue the
 * same thread (e.g. answering a follow-up question); omit it to start a new
 * conversation.
 */
export interface OrchestratorResponse {
  conversation_id: string;
  kind:
    | "question"
    | "confirm_transaction"
    | "estimate_result"
    | "sales_goal_result"
    | "financial_recommendation_result"
    | "period_summary_result"
    | "agent_unavailable"
    | "error";
  message: string | null;
  message_params: Record<string, string> | null;
  draft: ParsedTransaction | null;
  estimate: ProductionEstimate | null;
  sales_goal: SalesGoalResult | null;
  financial_recommendation: FinancialRecommendationResult | null;
  period_summary: PeriodSummaryResult | null;
  agent: UnavailableAgent | null;
  error_code: string | null;
}
