/**
 * File: Message.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: UI component for rendering individual chat bubbles. 
 *              Handles the polymorphic display of text, SQL code, 
 *              tabular data, and interactive visualizations based on 
 *              the backend response payload.
 */

'use client';

import { AlertTriangle, Bot, User, Sparkles } from 'lucide-react';
import { ChartRenderer } from '@/components/Renderers/ChartRenderer';
import { SqlBlock } from '@/components/Renderers/SqlBlock';
import { TableRenderer } from '@/components/Renderers/TableRenderer';
import type { ChatMessage } from '@/lib/types';
import { LoadingDots } from './LoadingDots';

interface Props {
  /** The message object containing metadata, roles, and response payloads. */
  message: ChatMessage;
}

/**
 * Message Component
 * 
 * Orchestrates the "Assistant" and "User" visual states. For assistant 
 * messages, it conditionally renders analytical sub-components (Charts, Tables) 
 * if they are present in the response payload.
 */
export function Message({ message }: Props) {
  // --- User Message View ---
  if (message.role === 'user') {
    return (
      <div className="flex gap-4 animate-in slide-in-from-right-4 duration-300">
        <div className="w-10 h-10 rounded-xl bg-muted/20 border border-border/50 flex items-center justify-center shrink-0 shadow-sm">
          <User className="w-5 h-5 text-muted-foreground" />
        </div>
        <div className="bg-primary/5 border border-primary/20 rounded-2xl rounded-tl-none px-5 py-3 text-sm text-foreground/90 shadow-sm max-w-[85%] leading-relaxed">
          {message.text}
        </div>
      </div>
    );
  }

  // --- Assistant Message View ---
  return (
    <div className="flex gap-4 animate-in slide-in-from-left-4 duration-500">
      <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 shadow-md">
        <Bot className="w-5 h-5 text-primary" />
      </div>
      
      <div className="flex-1 flex flex-col gap-4 max-w-[90%]">
        {/* Pending State */}
        {message.pending ? (
          <div className="bg-muted/10 border border-border/30 rounded-2xl rounded-tl-none px-6 py-4 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <LoadingDots />
              <span className="text-xs text-muted-foreground font-medium animate-pulse">Analyzing database schema...</span>
            </div>
          </div>
        ) : message.payload?.error ? (
          /* Error Feedback View */
          <div className="bg-red-500/5 border border-red-500/20 rounded-2xl rounded-tl-none px-5 py-4 flex gap-3 items-start shadow-lg">
            <div className="p-1.5 bg-red-500/10 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-red-500" />
            </div>
            <div className="text-sm">
              <p className="font-bold text-red-500 mb-1 uppercase tracking-tight text-xs">Pipeline Execution Error</p>
              <p className="text-foreground/90 font-medium leading-relaxed">{message.payload.error.message}</p>
              <p className="text-xs text-muted-foreground/80 mt-2 bg-black/20 p-2 rounded border border-border/10 italic">
                {message.payload.error.hint}
              </p>
              {message.payload.sql && (
                <div className="mt-4 pt-4 border-t border-red-500/10">
                  <SqlBlock sql={message.payload.sql} />
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Successful Insight View */
          <>
            {/* 1. Natural Language Insights / Clarification */}
            {message.payload?.insights && (
              <div className={`bg-muted/10 border border-border/30 rounded-2xl rounded-tl-none px-6 py-4 text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed backdrop-blur-md shadow-xl relative overflow-hidden group ${message.payload.needs_clarification ? 'border-amber-500/30 bg-amber-500/5' : ''}`}>
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-30 transition-opacity">
                   {message.payload.needs_clarification ? (
                     <AlertTriangle className="w-4 h-4 text-amber-500" />
                   ) : (
                     <Sparkles className="w-4 h-4 text-primary" />
                   )}
                </div>
                {message.payload.needs_clarification && (
                  <p className="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                    Ambiguity Detected
                  </p>
                )}
                {message.payload.insights}
              </div>
            )}
            
            {/* 2. Visualization (Chart) */}
            {message.payload?.chart && (
              <div className="animate-in zoom-in-95 duration-500 delay-150">
                <ChartRenderer spec={message.payload.chart} />
              </div>
            )}
            
            {/* 3. Raw Data (Table) */}
            {message.payload?.table && message.payload.table.rows.length > 0 && (
              <div className="animate-in zoom-in-95 duration-500 delay-300">
                <TableRenderer table={message.payload.table} />
              </div>
            )}
            
            {/* 4. Technical Audit (SQL) */}
            {message.payload?.sql && (
              <div className="animate-in fade-in duration-700 delay-500">
                <SqlBlock sql={message.payload.sql} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
