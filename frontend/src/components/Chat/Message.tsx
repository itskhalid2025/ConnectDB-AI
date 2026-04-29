'use client';

import { AlertTriangle, Bot, User } from 'lucide-react';

import { ChartRenderer } from '@/components/Renderers/ChartRenderer';
import { SqlBlock } from '@/components/Renderers/SqlBlock';
import { TableRenderer } from '@/components/Renderers/TableRenderer';
import type { ChatMessage } from '@/lib/types';

import { LoadingDots } from './LoadingDots';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  if (message.role === 'user') {
    return (
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-panelHover flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-muted" />
        </div>
        <div className="bg-panel border border-border rounded-lg px-4 py-2 text-sm text-text">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center shrink-0">
        <Bot className="w-4 h-4 text-accent" />
      </div>
      <div className="flex-1 flex flex-col gap-3">
        {message.pending ? (
          <div className="bg-panel border border-border rounded-lg px-4 py-3">
            <LoadingDots />
          </div>
        ) : message.payload?.error ? (
          <div className="bg-danger/10 border border-danger/40 rounded-lg px-4 py-3 flex gap-2 items-start">
            <AlertTriangle className="w-4 h-4 text-danger mt-0.5" />
            <div className="text-sm text-text">
              <p className="font-medium text-danger mb-1">{message.payload.error.message}</p>
              <p className="text-xs text-muted">{message.payload.error.hint}</p>
              {message.payload.sql && (
                <div className="mt-2">
                  <SqlBlock sql={message.payload.sql} />
                </div>
              )}
            </div>
          </div>
        ) : (
          <>
            {message.payload?.insights && (
              <div className="bg-panel border border-border rounded-lg px-4 py-3 text-sm text-text whitespace-pre-wrap">
                {message.payload.insights}
              </div>
            )}
            {message.payload?.chart && <ChartRenderer spec={message.payload.chart} />}
            {message.payload?.table && message.payload.table.rows.length > 0 && (
              <TableRenderer table={message.payload.table} />
            )}
            {message.payload?.sql && <SqlBlock sql={message.payload.sql} />}
          </>
        )}
      </div>
    </div>
  );
}
