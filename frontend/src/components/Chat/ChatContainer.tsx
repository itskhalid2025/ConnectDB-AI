'use client';

import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';

export function ChatContainer() {
  return (
    <main className="flex-1 flex flex-col h-screen bg-bg">
      <MessageList />
      <ChatInput />
    </main>
  );
}
