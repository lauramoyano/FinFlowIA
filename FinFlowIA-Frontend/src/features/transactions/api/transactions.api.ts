import apiClient from "@/shared/lib/api-client";
import type { ApiResponse, PaginatedResponse } from "@/shared/types/api.types";
import type {
  CreateTransactionRequest,
  OrchestratorResponse,
  ParsedTransaction,
  Transaction,
  TransactionFilters,
  UpdateTransactionRequest,
} from "@/features/transactions/types/transaction.types";
import type { UUID } from "@/shared/types/common.types";

export const transactionsApi = {
  list: async (filters: TransactionFilters = {}): Promise<PaginatedResponse<Transaction>> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        params.append(key, String(value));
      }
    });
    const response = await apiClient.get<PaginatedResponse<Transaction>>(
      `/transactions?${params.toString()}`,
    );
    return response.data;
  },

  getById: async (id: UUID): Promise<Transaction> => {
    const response = await apiClient.get<ApiResponse<Transaction>>(
      `/transactions/${id}`,
    );
    return response.data.data;
  },

  create: async (data: CreateTransactionRequest): Promise<Transaction> => {
    const response = await apiClient.post<ApiResponse<Transaction>>(
      "/transactions",
      data,
    );
    return response.data.data;
  },

  parseText: async (text: string): Promise<ParsedTransaction> => {
    const response = await apiClient.post<ApiResponse<ParsedTransaction>>(
      "/transactions/parse",
      { text },
    );
    return response.data.data;
  },

  update: async (id: UUID, data: UpdateTransactionRequest): Promise<Transaction> => {
    const response = await apiClient.put<ApiResponse<Transaction>>(
      `/transactions/${id}`,
      data,
    );
    return response.data.data;
  },

  delete: async (id: UUID): Promise<void> => {
    await apiClient.delete(`/transactions/${id}`);
  },
};

export const orchestratorApi = {
  sendMessage: async (
    conversationId: string | null,
    text: string,
  ): Promise<OrchestratorResponse> => {
    const response = await apiClient.post<ApiResponse<OrchestratorResponse>>(
      "/orchestrator/message",
      { conversation_id: conversationId, text },
    );
    return response.data.data;
  },
};
