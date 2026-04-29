/**
 * File: BusinessNotesPanel.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Interface for providing domain-specific context to the AI.
 *              Allows users to define custom business metrics or acronyms 
 *              to improve SQL generation accuracy.
 */

'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { useSession } from '@/store/sessionStore';

/**
 * BusinessNotesPanel Component
 * 
 * Renders a persistent text area for business context. Changes are 
 * auto-saved on blur to the backend session, ensuring the SQL generator 
 * always has access to the latest definitions.
 */
export function BusinessNotesPanel() {
  const { sessionId, notes, setNotes } = useSession();
  const [draft, setDraft] = useState(notes);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  /**
   * Keep the local draft in sync if the global store changes 
   * (e.g. from a session reload or reset).
   */
  useEffect(() => {
    setDraft(notes);
  }, [notes]);

  /**
   * Persists the draft notes to both the local store and the backend API.
   */
  const handleSave = async () => {
    if (draft === notes) return; // Optimisation: Skip if no changes

    setNotes(draft);
    if (sessionId) {
      try {
        await api.saveNotes(sessionId, draft);
        setSavedAt(new Date().toLocaleTimeString());
      } catch {
        // Silently handle save failure; notes remain in local state memory.
      }
    }
  };

  return (
    <Card title="Knowledge Base (Context)">
      <div className="space-y-3">
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          Define metrics (e.g. <code className="text-primary/70">churn</code>) 
          or logic specific to your database to help the AI generate accurate SQL.
        </p>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleSave}
          disabled={!sessionId}
          rows={6}
          placeholder={
            sessionId
              ? 'e.g. "High value customer" = total_spend > 5000\n"Internal users" have @company.com emails.'
              : 'Establish a database connection to begin adding context…'
          }
          className="w-full bg-black/20 border border-border/50 rounded-lg px-3 py-2 text-xs text-foreground/90 resize-none focus:ring-1 focus:ring-primary/30 focus:border-primary/50 transition-all placeholder:text-muted-foreground/30 disabled:opacity-30 font-sans"
        />
        {savedAt && (
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-medium">
            <div className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
            Auto-saved at {savedAt}
          </div>
        )}
      </div>
    </Card>
  );
}
