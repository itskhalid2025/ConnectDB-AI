import clsx from 'clsx';
import { SelectHTMLAttributes, forwardRef } from 'react';

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export const Select = forwardRef<HTMLSelectElement, Props>(function Select(
  { label, className, children, ...rest },
  ref,
) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted">
      {label && <span>{label}</span>}
      <select
        ref={ref}
        className={clsx(
          'bg-bg border border-border rounded-md px-3 py-2 text-sm text-text',
          'focus:outline-none focus:border-accent disabled:opacity-50',
          className,
        )}
        {...rest}
      >
        {children}
      </select>
    </label>
  );
});
