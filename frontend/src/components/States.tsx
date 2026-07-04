import { AlertOctagon, Inbox, Loader2 } from "lucide-react";

export function Loading({ label = "Chargement..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-ink-faint">
      <Loader2 className="h-5 w-5 animate-spin" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-status-critical/30 bg-status-critical/10 p-4 text-sm text-status-critical">
      <AlertOctagon className="h-5 w-5 shrink-0" />
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border p-10 text-center text-ink-faint">
      <Inbox className="h-6 w-6" />
      <span className="text-sm">{message}</span>
    </div>
  );
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return <div className={`skeleton h-24 rounded-xl ${className}`} />;
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
