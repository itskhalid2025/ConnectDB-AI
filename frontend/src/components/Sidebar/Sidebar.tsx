/**
 * File: Sidebar.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Primary layout component for application configuration.
 *              Houses the database connection form, AI engine settings, 
 *              and provides a real-time overview of the introspected schema.
 */

'use client';

import { Database, LayoutGrid } from 'lucide-react';
import { useSession } from '@/store/sessionStore';
import { AIConfigPanel } from './AIConfigPanel';
import { BusinessNotesPanel } from './BusinessNotesPanel';
import { ConnectionForm } from './ConnectionForm';

/**
 * Sidebar Component
 * 
 * Acts as the "Control Center" for the analytical workflow. Includes 
 * state-driven conditional rendering for the database schema visualization.
 */
export function Sidebar() {
  const { schema } = useSession();

  return (
    <aside className="w-80 shrink-0 h-screen overflow-y-auto bg-muted/20 border-r border-border/60 p-5 flex flex-col gap-5 backdrop-blur-md custom-scrollbar">
      {/* Branding Section */}
      <header className="flex items-center gap-3 text-foreground py-2 mb-2">
        <div className="p-2 bg-primary/10 rounded-xl border border-primary/20 shadow-inner">
          <Database className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight leading-none">ConnectDB AI</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1 font-semibold">Analytical Engine</p>
        </div>
      </header>

      {/* Configuration Modules */}
      <ConnectionForm />
      <AIConfigPanel />
      <BusinessNotesPanel />

      {/* Schema Visualization Panel */}
      {schema && (
        <div className="bg-muted/10 border border-border/40 rounded-xl p-4 shadow-sm">
          <header className="flex items-center justify-between mb-3">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
              <LayoutGrid className="w-3 h-3" />
              Database Schema
            </h3>
            <span className="text-[10px] font-mono text-primary/70 bg-primary/10 px-1.5 py-0.5 rounded">
              {schema.tables.length} Objects
            </span>
          </header>
          
          <ul className="text-[11px] text-muted-foreground max-h-56 overflow-y-auto space-y-1.5 font-mono custom-scrollbar pr-2">
            {schema.tables.slice(0, 50).map((t) => (
              <li 
                key={`${t.schema}.${t.name}`} 
                className="truncate group flex items-center gap-2 hover:text-foreground transition-colors cursor-default" 
                title={`${t.schema}.${t.name}`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-border group-hover:bg-primary/50 transition-colors" />
                <span>
                  {t.schema === 'public' ? t.name : `${t.schema}.${t.name}`}
                </span>
                <span className="text-[9px] opacity-40 ml-auto">
                  {t.columns.length} cols
                </span>
              </li>
            ))}
            {schema.tables.length > 50 && (
              <li className="text-[10px] text-muted-foreground/50 italic py-1 border-t border-border/20 mt-2">
                ...and {schema.tables.length - 50} additional tables
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Versioning Footnote */}
      <footer className="mt-auto pt-8 flex justify-center">
        <p className="text-[10px] font-mono text-muted-foreground/30">ConnectDB UI Engine v1.1.0</p>
      </footer>
    </aside>
  );
}
