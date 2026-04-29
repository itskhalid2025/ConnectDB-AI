import { ChatContainer } from '@/components/Chat/ChatContainer';
import { Sidebar } from '@/components/Sidebar/Sidebar';

export default function HomePage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-text">
      <Sidebar />
      <ChatContainer />
    </div>
  );
}
