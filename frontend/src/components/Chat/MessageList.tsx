/**
 * File: MessageList.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Container for the chat history. Handles empty states, 
 *              sequential rendering of message turns, and automatic 
 *              scroll-to-bottom behavior.
 */

'use client';

import { useEffect, useRef } from 'react';
import { useSession } from '@/store/sessionStore';
import { Message } from './Message';

/**
 * MessageList Component
 * 
 * Manages the viewport for the conversation. Provides helpful onboarding 
 * suggestions when the message history is empty.
 */
export function MessageList() {
  const messages = useSession((s) => s.messages);
  const endRef = useRef<HTMLDivElement | null>(null);

  /**
   * Automatically scroll the chat window to the latest message.
   * Triggered whenever the messages array updates.
   */
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Empty State: Onboarding Suggestion View
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm px-6 text-center animate-in fade-in duration-700">
        <div className="max-w-md space-y-4">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/5 flex items-center justify-center border border-primary/10 mb-4">
            <span className="text-xl">✨</span>
          </div>
          <h2 className="text-foreground font-semibold text-base">Intelligent Data Analysis Ready</h2>
          <p className="leading-relaxed">
            Connect your database and ask natural language questions like:<br/>
            <span className="italic text-primary/70 mt-2 block font-medium">
              &ldquo;What is the average transaction value by month?&rdquo;
            </span>
            <span className="italic text-primary/70 block font-medium">
              &ldquo;Show me a heatmap of user activity by region.&rdquo;
            </span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 custom-scrollbar scroll-smooth">
      <div className="max-w-4xl mx-auto flex flex-col gap-8">
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}
        {/* Scroll anchor */}
        <div ref={endRef} className="h-4" />
      </div>
    </div>
  );
}
