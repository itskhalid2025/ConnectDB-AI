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
