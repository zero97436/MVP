import { AnimatePresence, motion } from "framer-motion";
import { ArrowDownCircle, ArrowUpCircle, Radio, RefreshCw } from "lucide-react";
import { useLiveEvents, type LiveEvent } from "../../hooks/useLiveEvents";
import { statusMeta } from "../../lib/status";
import { timeAgo } from "../../lib/format";
import { cn } from "../../lib/cn";

const KIND_META: Record<LiveEvent["kind"], { label: string; icon: typeof Radio }> = {
  new: { label: "Nouvelle alerte", icon: ArrowUpCircle },
  changed: { label: "Changement d'état", icon: RefreshCw },
  resolved: { label: "Résolu", icon: ArrowDownCircle },
};

export function LiveEventFeed({ height = 320 }: { height?: number }) {
  const { events, connected } = useLiveEvents();

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          <Radio className="h-4 w-4" /> Live Monitoring
        </h2>
        <span className="flex items-center gap-1.5 text-xs text-ink-faint">
          <span
            className={cn(
              "inline-block h-2 w-2 rounded-full",
              connected ? "bg-status-ok animate-pulse-ring" : "bg-status-unknown",
            )}
          />
          {connected ? "En direct" : "Connexion..."}
        </span>
      </div>

      <div className="space-y-2 overflow-y-auto pr-1" style={{ maxHeight: height }}>
        {events.length === 0 ? (
          <p className="py-10 text-center text-sm text-ink-faint">
            En attente d'événements… les changements d'état apparaîtront ici en temps réel.
          </p>
        ) : (
          <AnimatePresence initial={false}>
            {events.map((e) => {
              const meta = statusMeta(e.status);
              const kind = KIND_META[e.kind];
              const Icon = kind.icon;
              return (
                <motion.div
                  key={e.id}
                  layout
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-start gap-3 rounded-lg border border-border bg-bg-soft/60 p-2.5"
                >
                  <span className={cn("mt-0.5 rounded-md p-1.5", meta.soft)}>
                    <Icon className="h-3.5 w-3.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-ink">
                      {kind.label} · <span className={meta.text}>{e.status}</span>
                    </p>
                    <p className="truncate text-xs text-ink-soft">
                      {e.hostName} / {e.checkName}
                    </p>
                  </div>
                  <span className="shrink-0 text-[11px] text-ink-faint">{timeAgo(new Date(e.at).toISOString())}</span>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
