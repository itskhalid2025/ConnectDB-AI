/**
 * File: types.ts
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: TypeScript interface definitions. Mirrors the backend Pydantic 
 *              models to ensure end-to-end type safety for API requests and responses.
 */

/** Supported AI Providers */
export type Provider = 'openai' | 'gemini' | 'anthropic';

/** Configuration for connecting to a PostgreSQL instance. */
export interface PostgresCredentials {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  sslmode?: string;
}

/** Basic metadata for a database column. */
export interface ColumnInfo {
  name: string;
  data_type: string;
  is_nullable: boolean;
}

/** Describes a relationship between tables. */
export interface ForeignKey {
  column: string;
  references_table: string;
  references_column: string;
}

/** Detailed metadata for a database table. */
export interface TableInfo {
  schema: string;
  name: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKey[];
  approx_row_count: number | null;
}

/** Collection of all tables in the database schema. */
export interface SchemaSummary {
  tables: TableInfo[];
}

/** User preferences for AI model and credentials. */
export interface AIConfig {
  provider: Provider;
  api_key: string;
  model: string;
}

/** Basic metadata for a supported AI model. */
export interface ModelInfo {
  id: string;
  label: string;
}

/** Results of a SQL query execution. */
export interface TableResult {
  columns: string[];
  rows: unknown[][];
  truncated: boolean;
}

/** Visualization configuration compatible with Plotly. */
export interface ChartSpec {
  data: Array<Record<string, unknown>>;
  layout: Record<string, unknown>;
}

/** Standardized error payload from the backend pipeline. */
export interface ErrorPayload {
  stage: string;
  message: string;
  hint: string;
}

/** Unified response from the chat orchestrator. */
export interface ChatResponse {
  message_id: string;
  sql: string | null;
  table: TableResult | null;
  chart: ChartSpec | null;
  insights: string | null;
  error: ErrorPayload | null;
  // --- New Fields for v2.0.0 ---
  classification: string | null;
  explanation: string | null;
  needs_clarification: boolean;
}

/** Roles permitted in the chat history. */
export type MessageRole = 'user' | 'assistant';

/** Internal representation of a single chat turn in the UI. */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  /** For user: the raw input. For assistant: the response summary. */
  text: string;
  /** Complete result payload for assistant turns. */
  payload?: ChatResponse;
  /** UI flag for messages currently being generated. */
  pending?: boolean;
}
