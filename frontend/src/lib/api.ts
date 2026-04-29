/**
 * File: api.ts
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Specialized API client for the ConnectDB backend. 
 *              Handles HTTP communication, unified error parsing, and 
 *              type-safe request/response mapping.
 */

import type {
  AIConfig,
  ChatResponse,
  ModelInfo,
  PostgresCredentials,
  Provider,
  SchemaSummary,
} from './types';

// Use environment variable or fallback to local backend default
const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom error class that preserves backend-specific stage and hint information.
 * Used to provide actionable feedback to the user in the UI.
 */
class ApiError extends Error {
  hint: string;
  stage: string;
  constructor(message: string, hint: string, stage: string) {
    super(message);
    this.hint = hint;
    this.stage = stage;
  }
}

/**
 * Base fetch wrapper with standardized error interceptors.
 * 
 * @param path The API endpoint path.
 * @param init Optional fetch configuration.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    let hint = `Request failed (${res.status})`;
    let stage = 'http';
    let message = hint;

    try {
      const body = await res.json();
      // Prioritize structured backend errors (ConnectDBError)
      if (body?.error) {
        message = body.error.message ?? message;
        hint = body.error.hint ?? hint;
        stage = body.error.stage ?? stage;
      } else if (body?.detail) {
        // Fallback for standard FastAPI validation errors
        message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        hint = message;
      }
    } catch {
      /* ignore JSON parse failure on raw HTTP errors */
    }
    
    throw new ApiError(message, hint, stage);
  }

  return (await res.json()) as T;
}

/**
 * Singleton API service object providing methods for all backend interactions.
 */
export const api = {
  /** Validates credentials without creating a session. */
  testConnection: (creds: PostgresCredentials) =>
    request<{ ok: boolean; server_version?: string; error?: string }>(
      '/api/connections/test',
      { method: 'POST', body: JSON.stringify(creds) },
    ),

  /** Establishes a persistence session and returns the introspected schema. */
  connect: (creds: PostgresCredentials) =>
    request<{ session_id: string; schema_summary: SchemaSummary }>(
      '/api/connections/connect',
      { method: 'POST', body: JSON.stringify(creds) },
    ),

  /** Explicitly closes the session and connection pool. */
  deleteSession: (sessionId: string) =>
    request<{ ok: boolean }>(`/api/sessions/${sessionId}`, { method: 'DELETE' }),

  /** Persists domain-specific context (notes) for the SQL generator. */
  saveNotes: (sessionId: string, notes: string) =>
    request<{ ok: boolean }>(`/api/sessions/${sessionId}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ notes }),
    }),

  /** Retrieves available models for a specific AI provider. */
  listModels: (provider: Provider, apiKey: string) =>
    request<{ provider: Provider; models: ModelInfo[] }>(
      `/api/llm/models?provider=${encodeURIComponent(provider)}&api_key=${encodeURIComponent(apiKey)}`,
    ),

  /** Submits a question to the analytical pipeline. */
  sendMessage: (sessionId: string, question: string, aiConfig: AIConfig) =>
    request<ChatResponse>(`/api/chat/${sessionId}/message`, {
      method: 'POST',
      body: JSON.stringify({ question, ai_config: aiConfig }),
    }),
};

export { ApiError };
