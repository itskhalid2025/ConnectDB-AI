/**
 * ============================================================
 * FILE: sessionStore.ts
 * PATH: frontend/src/store/sessionStore.ts
 * ============================================================
 * DESCRIPTION:
 *   Global state management using Zustand with Persistence. 
 *   Centralizes session state and synchronizes it with 
 *   sessionStorage to preserve data across refreshes.
 *
 * CREATED: 2026-04-25 | 10:00 AM
 *
 * EDIT LOG:
 * ─────────────────────────────────────────────────────────────
 * [2026-04-25 | 10:00 AM] - Initial file created.
 * [2026-05-09 | 01:09 PM] - Standardized file header and JSDoc.
 * ─────────────────────────────────────────────────────────────
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type {
  AIConfig,
  ChatMessage,
  ModelInfo,
  PostgresCredentials,
  Provider,
  SchemaSummary,
} from '@/lib/types';

/** Represents the current connectivity status of the application. */
type ConnectionState = 'disconnected' | 'connecting' | 'connected';

/**
 * Interface for the primary session state store.
 */
interface SessionState {
  // --- Database Connection State ---
  credentials: PostgresCredentials;
  setCredentials: (c: Partial<PostgresCredentials>) => void;
  connectionState: ConnectionState;
  setConnectionState: (s: ConnectionState) => void;
  sessionId: string | null;
  schema: SchemaSummary | null;
  connect: (sessionId: string, schema: SchemaSummary) => void;
  disconnect: () => void;

  // --- AI Configuration State ---
  provider: Provider;
  apiKey: string;
  model: string;
  models: ModelInfo[];
  modelsLoading: boolean;
  setProvider: (p: Provider) => void;
  setApiKey: (k: string) => void;
  setModel: (m: string) => void;
  setModels: (m: ModelInfo[]) => void;
  setModelsLoading: (b: boolean) => void;
  /** Helper to construct a validated AIConfig object for API calls. */
  aiConfig: () => AIConfig | null;

  // --- Domain Context (Notes) ---
  notes: string;
  setNotes: (n: string) => void;

  // --- Chat & Interaction History ---
  messages: ChatMessage[];
  addMessage: (m: ChatMessage) => void;
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;
  clearMessages: () => void;
}

/** Sensible defaults for the connection form. */
const DEFAULT_CREDS: PostgresCredentials = {
  host: 'localhost',
  port: 5432,
  database: '',
  user: 'postgres',
  password: '',
  sslmode: 'prefer',
};

/**
 * Global hook for accessing and mutating session state.
 * Includes Persistence Middleware:
 * - Persists to 'sessionStorage' (survives refreshes, cleared on tab close).
 */
export const useSession = create<SessionState>()(
  persist(
    (set, get) => ({
      // Connection management
      credentials: DEFAULT_CREDS,
      setCredentials: (c) => set((s) => ({ credentials: { ...s.credentials, ...c } })),
      connectionState: 'disconnected',
      setConnectionState: (connectionState) => set({ connectionState }),
      sessionId: null,
      schema: null,
      connect: (sessionId, schema) =>
        set({ sessionId, schema, connectionState: 'connected', messages: [] }),
      disconnect: () =>
        set({ sessionId: null, schema: null, connectionState: 'disconnected', messages: [] }),

      // AI Configuration
      provider: 'openai',
      apiKey: '',
      model: '',
      models: [],
      modelsLoading: false,
      setProvider: (provider) => set({ provider, model: '', models: [] }),
      setApiKey: (apiKey) => set({ apiKey, model: '', models: [] }),
      setModel: (model) => set({ model }),
      setModels: (models) => set({ models }),
      setModelsLoading: (modelsLoading) => set({ modelsLoading }),
      aiConfig: () => {
        const { provider, apiKey, model } = get();
        if (!apiKey || !model) return null;
        return { provider, api_key: apiKey, model };
      },

      // Business context
      notes: '',
      setNotes: (notes) => set({ notes }),

      // Message list management
      messages: [],
      addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
      updateMessage: (id, patch) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
        })),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'connectdb-ai-session',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
