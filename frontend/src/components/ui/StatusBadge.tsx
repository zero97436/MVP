import type { CheckStatus } from "../../types";
import { statusMeta } from "../../lib/status";
import { cn } from "../../lib/cn";

export function StatusBadge({
  status,
  label,
  size = "sm",
}: {
  status?: CheckStatus | null;
  label?: string;
  size?: "xs" | "sm";
}) {
  const s = status ?? "UNKNOWN";
  const meta = statusMeta(s);
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium",
        meta.soft,
        size === "xs" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
      )}
    >
      <Icon className={size === "xs" ? "h-3 w-3" : "h-3.5 w-3.5"} />
      {label ?? s}
    </span>
  );
}

export function StatusDot({ status, pulse }: { status?: CheckStatus | null; pulse?: boolean }) {
  const meta = statusMeta(status);
  return (
    <span className="relative inline-flex h-2.5 w-2.5">
      {pulse && (
        <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-60", meta.dot, "animate-ping")} />
      )}
      <span className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", meta.dot)} />
    </span>
  );
}
