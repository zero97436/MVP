import { useEffect, useState } from "react";
import {
  Bell, BellOff, CheckCheck, Wrench, Wand2, Activity, Loader2, ChevronDown, type LucideIcon,
} from "lucide-react";
import { listEvents } from "../api/endpoints";
import type { EventLog } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Loading, EmptyState } from "../components/States";
import { cn } from "../lib/cn";
import { timeAgo, formatDate } from "../lib/format";

const TYPE_META: Record<string, { label: string; icon: LucideIcon }> = {
  alert_opened: { label: "Alerte ouverte", icon: Bell },
  alert_resolved: { label: "Alerte résolue", icon: CheckCheck },
  alert_suppressed: { label: "Alerte supprimée (maintenance)", icon: BellOff },
  alert_acknowledged: { label: "Incident acquitté", icon: CheckCheck },
  alert_unacknowledged: { label: "Acquittement retiré", icon: Bell },
  maintenance_created: { label: "Maintenance planifiée", icon: Wrench },
  maintenance_deleted: { label: "Maintenance supprimée", icon: Wrench },
  remediation: { label: "Remédiation", icon: Wand2 },
};

const LEVEL_COLOR: Record<string, string> = {
  info: "bg-status-info/15 text-status-info",
  warning: "bg-status-warning/15 text-status-warning",
  critical: "bg-status-critical/15 text-status-critical",
};

const FILTERS: { value: string; label: string }[] = [
  { value: "", label: "Tous" },
  { value: "alert_opened", label: "Alertes" },
  { value: "alert_acknowledged", label: "Acquittements" },
  { value: "maintenance_created", label: "Maintenances" },
  { value: "remediation", label: "Remédiations" },
];

const PAGE = 50;

export default function EventsPage() {
  const [events, setEvents] = useState<EventLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    setLoading(true);
    listEvents({ type: filter || undefined, limit: PAGE, offset: 0 })
      .then((r) => {
        setEvents(r.data);
        setHasMore(r.data.length === PAGE);
      })
      .finally(() => setLoading(false));
  }, [filter]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const { data } = await listEvents({ type: filter || undefined, limit: PAGE, offset: events.length });
      setEvents((e) => [...e, ...data]);
      setHasMore(data.length === PAGE);
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Historique des événements" subtitle="Journal global : alertes, acquittements, maintenances, remédiations" />

      <div className="flex flex-wrap gap-1 rounded-lg border border-border bg-bg-soft p-1">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-medium transition",
              filter === f.value ? "bg-brand text-white" : "text-ink-soft hover:text-ink",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <Loading />
      ) : events.length === 0 ? (
        <EmptyState message="Aucun événement." />
      ) : (
        <Card className="p-0">
          <div className="divide-y divide-border">
            {events.map((e) => {
              const meta = TYPE_META[e.type] ?? { label: e.type, icon: Activity };
              const Icon = meta.icon;
              return (
                <div key={e.id} className="flex items-start gap-3 px-4 py-3">
                  <span className={cn("mt-0.5 rounded-lg p-1.5", LEVEL_COLOR[e.level] ?? LEVEL_COLOR.info)}>
                    <Icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-ink">
                      <span className="font-medium">{meta.label}</span>
                      {e.actor && e.actor !== "system" && <span className="text-ink-faint"> · {e.actor}</span>}
                    </p>
                    <p className="truncate text-xs text-ink-soft">{e.message}</p>
                  </div>
                  <span className="shrink-0 text-[11px] text-ink-faint" title={formatDate(e.created_at)}>
                    {timeAgo(e.created_at)}
                  </span>
                </div>
              );
            })}
          </div>
          {hasMore && (
            <button onClick={loadMore} disabled={loadingMore}
              className="flex w-full items-center justify-center gap-2 border-t border-border py-3 text-sm text-ink-soft hover:text-ink">
              {loadingMore ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronDown className="h-4 w-4" />}
              Charger plus
            </button>
          )}
        </Card>
      )}
    </div>
  );
}
