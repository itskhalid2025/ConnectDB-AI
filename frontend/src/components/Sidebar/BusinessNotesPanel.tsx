'use client';

import { useEffect, useState } from 'react';

import { Card } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { useSession } from '@/store/sessionStore';

export function BusinessNotesPanel() {
  const { sessionId, notes, setNotes } = useSession();
  const [draft, setDraft] = useState(notes);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    setDraft(notes);
  }, [notes]);

  const handleSave = async () => {
    setNotes(draft);
    if (sessionId) {
      try {
        await api.saveNotes(sessionId, draft);
        setSavedAt(new Date().toLocaleTimeString());
      } catch {
        // Surface the failure quietly — notes still cached locally.
      }
    }
  };

  return (
    <Card title="Business notes">
      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={handleSave}
        disabled={!sessionId}
        rows={6}
        placeholder={
          sessionId
            ? 'e.g. "Pass rate" = students with marks > 35.\n"Active users" logged in within 30 days.'
            : 'Connect to a database to add notes…'
        }
        className="w-full bg-bg border border-border rounded-md px-3 py-2 text-sm text-text resize-y focus:outline-none focus:border-accent disabled:opacity-50"
      />
      {savedAt && <p className="text-xs text-muted mt-2">Saved at {savedAt}</p>}
    </Card>
  );
}
