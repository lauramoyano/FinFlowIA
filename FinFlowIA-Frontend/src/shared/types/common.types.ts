export type UUID = string;

export type DateString = string; // ISO 8601 date: "2026-05-22"

export type DateTimeString = string; // ISO 8601 datetime: "2026-05-22T10:30:00Z"

export interface SelectOption<T = string> {
  label: string;
  value: T;
}

export type LoadingState = "idle" | "loading" | "success" | "error";

export interface WithId {
  id: UUID;
}

export interface WithTimestamps {
  created_at: DateTimeString;
  updated_at: DateTimeString;
}
