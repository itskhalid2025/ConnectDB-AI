'use client';

import dynamic from 'next/dynamic';

import type { ChartSpec } from '@/lib/types';

// Plotly is browser-only and large; load it on the client only.
const Plot = dynamic(() => import('react-plotly.js').then((m) => m.default), {
  ssr: false,
  loading: () => <div className="h-64 flex items-center justify-center text-muted">Loading chart…</div>,
});

interface Props {
  spec: ChartSpec;
}

export function ChartRenderer({ spec }: Props) {
  return (
    <div className="bg-bg border border-border rounded-md p-3">
      <Plot
        data={spec.data as never}
        layout={{
          ...spec.layout,
          autosize: true,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#e6e9f0', size: 12 },
        }}
        useResizeHandler
        style={{ width: '100%', height: 320 }}
        config={{ displaylogo: false, responsive: true }}
      />
    </div>
  );
}
