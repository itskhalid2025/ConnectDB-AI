'use client';

import { Send } from 'lucide-react';
import { useState } from 'react';

import { api, ApiError } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';
import { useSession } from '@/store/sessionStore';

export function ChatInput() {
  const { sessionId, aiConfig, addMessage, updateMessage, connectionState } = useSession();
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);

  const ai = aiConfig();
  const ready = connectionState === 'connected' && sessionId !== null && ai !== null;
  const placeholder = !ready
    ? connectionState !== 'connected'
      ? 'Connect to a database to start…'
      : 'Configure your AI provider and model to start…'
    : 'Ask a question about your data…';

  const send = async () => {
    if (!ready || !draft.trim() || busy || !sessionId || !ai) return;
    const question = draft.trim();
    setDraft('');
    setBusy(true);

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      text: question,
    };
    const assistantId = `a-${Date.now() + 1}`;
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      text: '',
      pending: true,
    };
    addMessage(userMsg);
    addMessage(assistantMsg);

    try {
      const res = await api.sendMessage(sessionId, question, ai);
      updateMessage(assistantId, { pending: false, payload: res });
    } catch (e) {
      const hint = e instanceof ApiError ? e.hint : 'Request failed.';
      updateMessage(assistantId, {
        pending: false,
        payload: {
          message_id: assistantId,
          sql: null,
          table: null,
          chart: null,
          insights: null,
          error: { stage: 'request', message: hint, hint },
        },
      });
    } finally {
      setBusy(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="border-t border-border bg-bg px-6 py-3">
      <div className="max-w-3xl mx-auto flex gap-2 items-end">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!ready || busy}
          placeholder={placeholder}
          rows={1}
          className="flex-1 bg-panel border border-border rounded-md px-3 py-2 text-sm text-text resize-none focus:outline-none focus:border-accent disabled:opacity-50 max-h-40"
        />
        <button
          onClick={send}
          disabled={!ready || busy || !draft.trim()}
          className="bg-accent hover:bg-accentHover text-white px-4 py-2 rounded-md disabled:bg-accent/40 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <Send className="w-4 h-4" />
          <span className="text-sm">Send</span>
        </button>
      </div>
    </div>
  );
}
