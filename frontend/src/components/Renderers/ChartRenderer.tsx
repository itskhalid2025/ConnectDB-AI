/**
 * ============================================================
 * FILE: ChartRenderer.tsx
 * PATH: frontend/src/components/Renderers/ChartRenderer.tsx
 * ============================================================
 * DESCRIPTION:
 *   Handles the rendering of interactive Plotly charts. 
 *   Uses dynamic imports and factory pattern to ensure 
 *   compatibility with Next.js SSR and client-side distribution.
 *
 * CREATED: 2026-04-25 | 10:00 AM
 *
 * EDIT LOG:
 * ─────────────────────────────────────────────────────────────
 * [2026-04-25 | 10:00 AM] - Initial file created.
 * [2026-05-08 | 12:24 PM] - Fixed ChunkLoadError by switching 
 *                           to factory pattern.
 * [2026-05-09 | 01:05 PM] - Standardized file header and JSDoc.
 * ─────────────────────────────────────────────────────────────
 */

'use client';

import dynamic from 'next/dynamic';
import type { ChartSpec } from '@/lib/types';

/**
 * Plotly is a heavy, browser-only library. 
 * We use Next.js dynamic imports to prevent SSR crashes and use the factory 
 * pattern to ensure correct distribution mapping.
 */
const Plot = dynamic(
  async () => {
    // Explicitly import both to ensure they are bundled correctly in a client-side chunk
    const Plotly = await import('plotly.js-dist-min');
    const createPlotlyComponent = (await import('react-plotly.js/factory')).default;
    return createPlotlyComponent(Plotly);
  },
  {
    ssr: false,
    loading: () => (
      <div className="h-64 flex items-center justify-center text-muted-foreground animate-pulse">
        Initialising visualisation engine…
      </div>
    ),
  }
);

interface Props {
  /** The standardized chart specification from the backend. */
  spec: ChartSpec;
}

/**
 * ChartRenderer Component
 * 
 * Takes a backend-generated Plotly specification and applies the global 
 * "glassmorphism" theme and responsive handlers.
 */
export function ChartRenderer({ spec }: Props) {
  return (
    <div className="bg-muted/10 border border-border/50 rounded-lg p-4 overflow-hidden backdrop-blur-sm shadow-xl">
      <Plot
        data={spec.data as any}
        layout={{
          ...spec.layout,
          autosize: true,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#e6e9f0', size: 12, family: 'Inter, sans-serif' },
          margin: { t: 40, r: 20, b: 40, l: 40 },
          // Enhanced visual styling for dark mode compatibility
          xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
          yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
        }}
        useResizeHandler
        style={{ width: '100%', height: '360px' }}
        config={{ 
          displaylogo: false, 
          responsive: true,
          modeBarButtonsToRemove: ['sendDataToCloud' as any, 'editInChartStudio' as any] 
        }}
      />
    </div>
  );
}
