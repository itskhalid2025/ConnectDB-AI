import { create } from 'zustand';

import type {
  AIConfig,
  ChatMessage,
  ModelInfo,
  PostgresCredentials,
  Provider,
  SchemaSummary,
} from '@/lib/types';

type ConnectionState = 'disconnected' | 'connecting' | 'connected';

interface SessionState {
  // connection
  credentials: PostgresCredentials;
  setCredentials: (c: Partial<PostgresCredentials>) => void;
  connectionState: ConnectionState;
  setConnectionState: (s: ConnectionState) => void;
  sessionId: string | null;
  schema: SchemaSummary | null;
  connect: (sessionId: string, schema: SchemaSummary) => void;
  disconnect: () => void;

  // ai config
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
  aiConfig: () => AIConfig | null;

  // notes
  notes: string;
  setNotes: (n: string) => void;

  // chat
  messages: ChatMessage[];
  addMessage: (m: ChatMessage) => void;
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;
  clearMessages: () => void;
}

const DEFAULT_CREDS: PostgresCredentials = {
  host: 'localhost',
  port: 5432,
  database: '',
  user: 'postgres',
  password: '',
  sslmode: 'prefer',
};

export const useSession = create<SessionState>((set, get) => ({
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

  notes: '',
  setNotes: (notes) => set({ notes }),

  messages: [],
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  updateMessage: (id, patch) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    })),
  clearMessages: () => set({ messages: [] }),
}));
