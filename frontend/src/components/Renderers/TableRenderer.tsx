/**
 * File: TableRenderer.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Data grid component for displaying structured SQL query results.
 *              Supports pagination, cell-type coercion, and high-performance 
 *              rendering of large datasets.
 */

'use client';

import { useState } from 'react';
import type { TableResult } from '@/lib/types';

interface Props {
  /** The tabular data and metadata returned by the backend. */
  table: TableResult;
}

/** Number of rows to display per page in the paginated view. */
const PAGE_SIZE = 25;

/**
 * Standardises cell content for display in the grid.
 * Handles complex objects by stringifying them and identifies nulls with a dash.
 */
function formatCell(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

/**
 * TableRenderer Component
 * 
 * Renders a high-density, monochromatic data grid optimized for analytical 
 * workflows. Includes built-in pagination to maintain UI responsiveness 
 * when dealing with thousands of rows.
 */
export function TableRenderer({ table }: Props) {
  const [page, setPage] = useState(0);

  // Guard: Handle empty result sets gracefully
  if (!table.columns.length) {
    return <p className="text-sm text-muted-foreground italic p-4">No rows returned by the query.</p>;
  }

  const totalPages = Math.max(1, Math.ceil(table.rows.length / PAGE_SIZE));
  const start = page * PAGE_SIZE;
  const slice = table.rows.slice(start, start + PAGE_SIZE);

  return (
    <div className="bg-bg border border-border/50 rounded-lg overflow-hidden backdrop-blur-sm shadow-md">
      <div className="overflow-x-auto">
        <table className="min-w-full text-[11px] leading-tight">
          <thead className="bg-muted/30">
            <tr>
              {table.columns.map((c) => (
                <th
                  key={c}
                  className="px-4 py-2.5 text-left font-semibold text-muted-foreground border-b border-border/60 uppercase tracking-wider whitespace-nowrap"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {slice.map((row, i) => (
              <tr key={i} className="hover:bg-primary/5 transition-colors duration-75">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className="px-4 py-2 text-foreground/90 font-mono border-b border-border/10 whitespace-nowrap"
                  >
                    {formatCell(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination & Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 text-[10px] text-muted-foreground bg-muted/20 border-t border-border/30">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground/70">
            {table.rows.length.toLocaleString()} row{table.rows.length === 1 ? '' : 's'}
          </span>
          {table.truncated && (
            <span className="bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded border border-amber-500/20 font-bold uppercase tracking-tighter">
              Truncated
            </span>
          )}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1 rounded-full hover:bg-muted transition-colors disabled:opacity-20"
              aria-label="Previous page"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <span className="font-mono">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1 rounded-full hover:bg-muted transition-colors disabled:opacity-20"
              aria-label="Next page"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
