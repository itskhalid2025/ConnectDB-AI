export function LoadingDots() {
  return (
    <div className="flex items-center gap-1 text-muted">
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:0ms]" />
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:120ms]" />
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:240ms]" />
    </div>
  );
}
