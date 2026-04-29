'use client';

import { useState } from 'react';

import type { TableResult } from '@/lib/types';

interface Props {
  table: TableResult;
}

const PAGE_SIZE = 25;

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

export function TableRenderer({ table }: Props) {
  const [page, setPage] = useState(0);

  if (!table.columns.length) {
    return <p className="text-sm text-muted italic">No rows returned.</p>;
  }

  const totalPages = Math.max(1, Math.ceil(table.rows.length / PAGE_SIZE));
  const start = page * PAGE_SIZE;
  const slice = table.rows.slice(start, start + PAGE_SIZE);

  return (
    <div className="bg-bg border border-border rounded-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead className="bg-panel">
            <tr>
              {table.columns.map((c) => (
                <th
                  key={c}
                  className="px-3 py-2 text-left font-medium text-muted border-b border-border whitespace-nowrap"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((row, i) => (
              <tr key={i} className="hover:bg-panelHover">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className="px-3 py-1.5 text-text font-mono border-b border-border/40 whitespace-nowrap"
                  >
                    {formatCell(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between px-3 py-2 text-xs text-muted bg-panel/60 border-t border-border">
        <span>
          {table.rows.length} row{table.rows.length === 1 ? '' : 's'}
          {table.truncated && ' (truncated)'}
        </span>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-1 rounded hover:bg-panelHover disabled:opacity-40"
            >
              ‹
            </button>
            <span>
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-1 rounded hover:bg-panelHover disabled:opacity-40"
            >
              ›
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
