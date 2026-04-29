/**
 * File: layout.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Root layout for the Next.js application. Configures 
 *              global styles, metadata (SEO), and core HTML structure.
 */

import type { Metadata, Viewport } from 'next';
import './globals.css';

/** 
 * SEO Metadata 
 * Standardised title and description for improved search visibility 
 * and browser tab identification.
 */
export const metadata: Metadata = {
  title: 'ConnectDB AI | Enterprise Analytical Assistant',
  description: 'Advanced AI-powered analytical assistant for PostgreSQL. Generate insights, charts, and audit SQL in real-time.',
  keywords: ['PostgreSQL', 'AI', 'Analytics', 'SQL Generation', 'Data Visualization'],
  authors: [{ name: 'ConnectDB AI Team' }],
};

/** Viewport configuration for responsive layout handling. */
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#0f172a', // Matches the deep slate theme
};

/**
 * RootLayout Component
 * 
 * Provides the foundational HTML structure. Includes hydration suppression 
 * to handle dynamic client-side only visualisations without UI flickering.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: 'dark' }}>
      <body className="antialiased font-sans bg-slate-950 text-slate-50 selection:bg-primary/30">
        {children}
      </body>
    </html>
  );
}
