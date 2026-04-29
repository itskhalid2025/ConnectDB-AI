import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'ConnectDB AI',
  description: 'AI-powered analytics assistant for PostgreSQL.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
