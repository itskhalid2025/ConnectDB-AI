// Mirrors of backend pydantic models — kept in one place so component imports stay tidy.

export type Provider = 'openai' | 'gemini' | 'anthropic';

export interface PostgresCredentials {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  sslmode?: string;
}

export interface ColumnInfo {
  name: string;
  data_type: string;
  is_nullable: boolean;
}

export interface ForeignKey {
  column: string;
  references_table: string;
  references_column: string;
}

export interface TableInfo {
  schema: string;
  name: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKey[];
  approx_row_count: number | null;
}

export interface SchemaSummary {
  tables: TableInfo[];
}

export interface AIConfig {
  provider: Provider;
  api_key: string;
  model: string;
}

export interface ModelInfo {
  id: string;
  label: string;
}

export interface TableResult {
  columns: string[];
  rows: unknown[][];
  truncated: boolean;
}

export interface ChartSpec {
  data: Array<Record<string, unknown>>;
  layout: Record<string, unknown>;
}

export interface ErrorPayload {
  stage: string;
  message: string;
  hint: string;
}

export interface ChatResponse {
  message_id: string;
  sql: string | null;
  table: TableResult | null;
  chart: ChartSpec | null;
  insights: string | null;
  error: ErrorPayload | null;
}

export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  /** For user messages: the question text. For assistant messages: empty (we use payload). */
  text: string;
  /** Set on assistant messages once the response arrives. */
  payload?: ChatResponse;
  pending?: boolean;
}
