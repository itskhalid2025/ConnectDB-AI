/**
 * ============================================================
 * FILE: page.tsx
 * PATH: frontend/src/app/page.tsx
 * ============================================================
 * DESCRIPTION:
 *   Primary entry point for the ConnectDB AI single-page 
 *   application. Sets up the horizontal split layout between 
 *   configuration (Sidebar) and analysis (Chat).
 *
 * CREATED: 2026-04-25 | 10:00 AM
 *
 * EDIT LOG:
 * ─────────────────────────────────────────────────────────────
 * [2026-04-25 | 10:00 AM] - Initial file created.
 * [2026-05-09 | 01:00 PM] - Standardized file header and JSDoc.
 * ─────────────────────────────────────────────────────────────
 */

import { ChatContainer } from '@/components/Chat/ChatContainer';
import { Sidebar } from '@/components/Sidebar/Sidebar';

/**
 * HomePage Component
 * 
 * Defines the root view hierarchy. Optimized for full-screen desktop 
 * analytical workflows with non-scrolling, viewport-constrained containers.
 */
export default function HomePage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground selection:bg-primary/20">
      {/* Configuration & Meta Panel */}
      <Sidebar />
      
      {/* Dynamic Analysis Viewport */}
      <ChatContainer />
    </div>
  );
}
