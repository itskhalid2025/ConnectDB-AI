'use client';

import { useEffect, useRef } from 'react';

import { useSession } from '@/store/sessionStore';

import { Message } from './Message';

export function MessageList() {
  const messages = useSession((s) => s.messages);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted text-sm px-6 text-center">
        <div className="max-w-md">
          <p className="mb-2 text-text">Ready when you are.</p>
          <p>
            Ask anything about your data — &ldquo;What is the pass rate?&rdquo;,
            &ldquo;Show monthly sales trend.&rdquo;, &ldquo;Top 10 products by revenue.&rdquo;
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
