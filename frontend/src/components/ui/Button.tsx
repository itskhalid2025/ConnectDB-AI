import clsx from 'clsx';
import { ButtonHTMLAttributes, forwardRef } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  fullWidth?: boolean;
}

const styles: Record<Variant, string> = {
  primary:
    'bg-accent hover:bg-accentHover text-white disabled:bg-accent/40 disabled:cursor-not-allowed',
  secondary:
    'bg-panelHover hover:bg-border text-text border border-border disabled:opacity-50 disabled:cursor-not-allowed',
  ghost:
    'bg-transparent hover:bg-panelHover text-text disabled:opacity-50 disabled:cursor-not-allowed',
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = 'primary', fullWidth, className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={clsx(
        'px-3 py-2 rounded-md text-sm font-medium transition-colors',
        styles[variant],
        fullWidth && 'w-full',
        className,
      )}
      {...rest}
    />
  );
});
