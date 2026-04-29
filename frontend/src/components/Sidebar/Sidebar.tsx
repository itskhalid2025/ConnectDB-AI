'use client';

import { Database } from 'lucide-react';

import { useSession } from '@/store/sessionStore';

import { AIConfigPanel } from './AIConfigPanel';
import { BusinessNotesPanel } from './BusinessNotesPanel';
import { ConnectionForm } from './ConnectionForm';

export function Sidebar() {
  const { schema } = useSession();

  return (
    <aside className="w-80 shrink-0 h-screen overflow-y-auto bg-panel/60 border-r border-border p-4 flex flex-col gap-4">
      <header className="flex items-center gap-2 text-text">
        <Database className="w-5 h-5 text-accent" />
        <h1 className="text-lg font-semibold">ConnectDB AI</h1>
      </header>

      <ConnectionForm />
      <AIConfigPanel />
      <BusinessNotesPanel />

      {schema && (
        <div className="bg-panel border border-border rounded-lg p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">
            Schema · {schema.tables.length} tables
          </h3>
          <ul className="text-xs text-muted max-h-40 overflow-y-auto space-y-1 font-mono">
            {schema.tables.slice(0, 50).map((t) => (
              <li key={`${t.schema}.${t.name}`} className="truncate" title={`${t.schema}.${t.name}`}>
                {t.schema === 'public' ? t.name : `${t.schema}.${t.name}`}
                <span className="text-muted/60"> ({t.columns.length})</span>
              </li>
            ))}
            {schema.tables.length > 50 && (
              <li className="text-muted/60">…and {schema.tables.length - 50} more</li>
            )}
          </ul>
        </div>
      )}
    </aside>
  );
}
