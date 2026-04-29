import type {
  AIConfig,
  ChatResponse,
  ModelInfo,
  PostgresCredentials,
  Provider,
  SchemaSummary,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  hint: string;
  stage: string;
  constructor(message: string, hint: string, stage: string) {
    super(message);
    this.hint = hint;
    this.stage = stage;
  }
}

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
      if (body?.error) {
        message = body.error.message ?? message;
        hint = body.error.hint ?? hint;
        stage = body.error.stage ?? stage;
      } else if (body?.detail) {
        message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        hint = message;
      }
    } catch {
      // ignore parse failure
    }
    throw new ApiError(message, hint, stage);
  }
  return (await res.json()) as T;
}

export const api = {
  testConnection: (creds: PostgresCredentials) =>
    request<{ ok: boolean; server_version?: string; error?: string }>(
      '/api/connections/test',
      { method: 'POST', body: JSON.stringify(creds) },
    ),

  connect: (creds: PostgresCredentials) =>
    request<{ session_id: string; schema_summary: SchemaSummary }>(
      '/api/connections/connect',
      { method: 'POST', body: JSON.stringify(creds) },
    ),

  deleteSession: (sessionId: string) =>
    request<{ ok: boolean }>(`/api/sessions/${sessionId}`, { method: 'DELETE' }),

  saveNotes: (sessionId: string, notes: string) =>
    request<{ ok: boolean }>(`/api/sessions/${sessionId}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ notes }),
    }),

  listModels: (provider: Provider, apiKey: string) =>
    request<{ provider: Provider; models: ModelInfo[] }>(
      `/api/llm/models?provider=${encodeURIComponent(provider)}&api_key=${encodeURIComponent(apiKey)}`,
    ),

  sendMessage: (sessionId: string, question: string, aiConfig: AIConfig) =>
    request<ChatResponse>(`/api/chat/${sessionId}/message`, {
      method: 'POST',
      body: JSON.stringify({ question, ai_config: aiConfig }),
    }),
};

export { ApiError };
