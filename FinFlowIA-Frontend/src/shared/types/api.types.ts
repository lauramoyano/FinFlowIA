export interface ApiResponse<T> {
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown[];
  };
  correlation_id?: string;
}
