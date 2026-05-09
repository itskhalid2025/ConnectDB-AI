/**
 * ============================================================
 * FILE: Card.tsx
 * PATH: src/components/ui/Card.tsx
 * ============================================================
 * DESCRIPTION:
 *   A reusable layout component for displaying content within 
 *   a styled card container with an optional title.
 *
 * CREATED: 2026-05-09 | 12:40 PM
 *
 * EDIT LOG:
 * ─────────────────────────────────────────────────────────────
 * [2026-05-09 | 12:40 PM] - Initial summary added.
 * [2026-05-09 | 12:45 PM] - Fixed Type 'ReactNode' conflict 
 *                           with HTML 'title' attribute using Omit.
 * ─────────────────────────────────────────────────────────────
 */
import clsx from 'clsx';
import { HTMLAttributes, ReactNode } from 'react';

interface Props extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: ReactNode;
  children: ReactNode;
}

export function Card({ title, children, className, ...rest }: Props) {
  return (
    <section
      className={clsx('bg-panel border border-border rounded-lg p-4', className)}
      {...rest}
    >
      {title && (
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
          {title}
        </h3>
      )}
      {children}
    </section>
  );
}
