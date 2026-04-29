/**
 * File: ChatContainer.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Primary layout container for the conversational interface.
 *              Manages the vertical stack of message history and query input.
 */

'use client';

import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';

/**
 * ChatContainer Component
 * 
 * Provides the main workspace for data analysis. Implements a flexbox 
 * column layout to ensure the input area remains anchored at the bottom 
 * while the message list occupies the remaining vertical space.
 */
export function ChatContainer() {
  return (
    <main className="flex-1 flex flex-col h-screen bg-background relative">
      {/* Scrollable conversation thread */}
      <MessageList />
      
      {/* Persistent query input bar */}
      <ChatInput />
    </main>
  );
}
