/**
 * File: ChatInput.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Primary input component for the analytical conversational interface.
 *              Manages input state, multi-line growth, and orchestrates the 
 *              message submission cycle with local state synchronization.
 */

'use client';

import { Send, Zap } from 'lucide-react';
import { useState } from 'react';
import { api, ApiError } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';
import { useSession } from '@/store/sessionStore';

/**
 * ChatInput Component
 * 
 * Renders an intelligent text area that disables itself based on the global 
 * connection and AI configuration status. Supports keyboard shortcuts (Enter to send).
 */
export function ChatInput() {
  const { sessionId, aiConfig, addMessage, updateMessage, connectionState } = useSession();
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);

  const ai = aiConfig();
  const isReady = connectionState === 'connected' && sessionId !== null && ai !== null;

  /** Dynamic placeholder logic based on current application readiness. */
  const placeholder = !isReady
    ? connectionState !== 'connected'
      ? 'Sync database to unlock analysis...'
      : 'Connect AI engine to begin...'
    : 'Ask a question about your datasets (e.g. "Monthly revenue trend")';

  /**
   * Orchestrates the message submission pipeline:
   * 1. Validates local and global readiness.
   * 2. Optimistically adds User and Pending Assistant messages.
   * 3. Executes the backend analytical request.
   * 4. Updates the Assistant message with the final payload or error.
   */
  const send = async () => {
    if (!isReady || !draft.trim() || busy || !sessionId || !ai) return;
    
    const question = draft.trim();
    setDraft('');
    setBusy(true);

    const timestamp = Date.now();
    const userMsg: ChatMessage = {
      id: `u-${timestamp}`,
      role: 'user',
      text: question,
    };
    
    const assistantId = `a-${timestamp + 1}`;
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      text: '',
      pending: true,
    };

    // Inject turns into the reactive store
    addMessage(userMsg);
    addMessage(assistantMsg);

    try {
      const res = await api.sendMessage(sessionId, question, ai);
      // Synchronize backend insight with the placeholder message
      updateMessage(assistantId, { pending: false, payload: res });
    } catch (e) {
      const hint = e instanceof ApiError ? e.hint : 'Communication failure with analytical engine.';
      updateMessage(assistantId, {
        pending: false,
        payload: {
          message_id: assistantId,
          sql: null,
          table: null,
          chart: null,
          insights: null,
          error: { stage: 'request', message: 'Engine Timeout', hint },
        },
      });
    } finally {
      setBusy(false);
    }
  };

  /** Helper for keyboard-based submission (standard chat UX). */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="border-t border-border/60 bg-muted/5 px-6 py-5 backdrop-blur-md">
      <div className="max-w-4xl mx-auto">
        <div className="relative flex items-end gap-3 bg-muted/10 border border-border/50 rounded-2xl p-2 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/40 transition-all shadow-lg group">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isReady || busy}
            placeholder={placeholder}
            rows={1}
            className="flex-1 bg-transparent border-none rounded-md px-4 py-3 text-sm text-foreground/90 resize-none focus:outline-none disabled:opacity-30 max-h-48 custom-scrollbar leading-relaxed"
          />
          <button
            onClick={send}
            disabled={!isReady || busy || !draft.trim()}
            className="bg-primary hover:bg-primary/90 text-primary-foreground p-3 rounded-xl disabled:bg-muted/40 disabled:cursor-not-allowed transition-all active:scale-95 shadow-md flex items-center gap-2 mb-1 mr-1"
            title="Submit Analysis"
          >
            {busy ? (
               <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span className="text-xs font-bold uppercase tracking-wider hidden sm:block">Run</span>
          </button>
        </div>
        
        {/* Input Footer Metadata */}
        <div className="flex justify-between items-center mt-3 px-2">
          <p className="text-[10px] text-muted-foreground font-medium flex items-center gap-1.5 opacity-60">
            <Zap className="w-3 h-3 text-amber-500/50" />
            ConnectDB SQL Guard active
          </p>
          <p className="text-[10px] text-muted-foreground font-mono opacity-30">Shift + Enter for new line</p>
        </div>
      </div>
    </div>
  );
}
