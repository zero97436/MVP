import { Activity, Database, Server, Cog, Workflow, CheckCircle2, XCircle } from "lucide-react";
import { getSystemHealth, type SystemHealth } from "../api/endpoints";
import { usePolling } from "../hooks/usePolling";
import { Card, SectionTitle } from "./ui/Card";
import { cn } from "../lib/cn";

const META: Record<string, { label: string; icon: typeof Database }> = {
  database: { label: "PostgreSQL", icon: Database },
  redis: { label: "Redis", icon: Server },
  celery_workers: { label: "Workers Celery", icon: Cog },
  scheduler: { label: "Scheduler", icon: Workflow },
};

function detail(name: string, c: { ok: boolean; [k: string]: unknown }): string {
  if (name === "database" && c.latency_ms != null) return `${c.latency_ms} ms`;
  if (name === "celery_workers") return `${c.count ?? 0} actif(s)`;
  if (name === "scheduler" && c.last_result_age_seconds != null) return `dernier résultat il y a ${c.last_result_age_seconds}s`;
  if (!c.ok && c.error) return String(c.error);
  return c.ok ? "OK" : "indisponible";
}

export function SystemHealthCard() {
  const { data } = usePolling<SystemHealth>(() => getSystemHealth().then((r) => r.data), 15000);
  if (!data) return null;

  return (
    <Card>
      <SectionTitle
        title="Santé de la plateforme"
        icon={Activity}
        action={
          <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium",
            data.status === "ok" ? "bg-status-ok/15 text-status-ok" : "bg-status-critical/15 text-status-critical")}>
            {data.status === "ok" ? "Tout est opérationnel" : "Dégradé"}
          </span>
        }
      />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {Object.entries(data.components).map(([name, c]) => {
          const m = META[name] ?? { label: name, icon: Activity };
          const Icon = m.icon;
          return (
            <div key={name} className="flex items-center gap-3 rounded-lg border border-border bg-bg-soft/50 px-3 py-2.5">
              <Icon className="h-4 w-4 text-ink-soft" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-ink">{m.label}</p>
                <p className="truncate text-xs text-ink-faint">{detail(name, c)}</p>
              </div>
              {c.ok
                ? <CheckCircle2 className="h-4 w-4 text-status-ok" />
                : <XCircle className="h-4 w-4 text-status-critical" />}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
