import clsx from 'clsx';
import { InputHTMLAttributes, forwardRef } from 'react';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { label, className, id, ...rest },
  ref,
) {
  const generatedId = id ?? rest.name;
  return (
    <label className="flex flex-col gap-1 text-xs text-muted">
      {label && <span>{label}</span>}
      <input
        ref={ref}
        id={generatedId}
        className={clsx(
          'bg-bg border border-border rounded-md px-3 py-2 text-sm text-text',
          'focus:outline-none focus:border-accent placeholder:text-muted/60',
          className,
        )}
        {...rest}
      />
    </label>
  );
});
