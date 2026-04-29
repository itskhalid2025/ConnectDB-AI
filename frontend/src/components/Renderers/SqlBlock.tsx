'use client';

import { ChevronDown, ChevronRight, Copy } from 'lucide-react';
import { useState } from 'react';

interface Props {
  sql: string;
}

export function SqlBlock({ sql }: Props) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard may be blocked
    }
  };

  return (
    <div className="bg-bg border border-border rounded-md text-xs">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 px-3 py-2 text-muted hover:text-text"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <span>View generated SQL</span>
      </button>
      {open && (
        <div className="border-t border-border">
          <div className="flex justify-end px-2 py-1">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-muted hover:text-text px-2 py-0.5 rounded"
            >
              <Copy className="w-3 h-3" />
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre className="font-mono text-text px-3 pb-3 overflow-x-auto whitespace-pre-wrap">
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
}
