import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Cpu, MemoryStick, HardDrive, Network, Server } from "lucide-react";
import { getHost, getHostMetrics, getHostMetricsHourly, listChecks, listResults } from "../api/endpoints";
import type { Check, CheckResult, Host, HostMetric, HostMetricHourly } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { MetricArea } from "../components/charts/MetricArea";
import { ErrorState, Loading } from "../components/States";
import { statusMeta, worstStatus } from "../lib/status";
import { uptimeSince, formatTime, formatDate } from "../lib/format";
import { metricStatus } from "../lib/series";

const WIDGETS = [
  { key: "CPU", field: "cpu_percent", hourly: "cpu_avg", icon: Cpu, color: "#3B82F6", unit: "%", base: 35, seed: 3 },
  { key: "RAM", field: "mem_percent", hourly: "mem_avg", icon: MemoryStick, color: "#8B5CF6", unit: "%", base: 55, seed: 7 },
  { key: "Disk", field: "disk_percent", hourly: "disk_avg", icon: HardDrive, color: "#F59E0B", unit: "%", base: 62, seed: 11 },
  { key: "Network", field: "net_mbps", hourly: "net_avg", icon: Network, color: "#10B981", unit: "Mb", base: 120, seed: 5 },
] as const;

export default function HostDetailPage() {
  const { id } = useParams();
  const hostId = Number(id);
  const [host, setHost] = useState<Host | null>(null);
  const [checks, setChecks] = useState<Check[]>([]);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [metrics, setMetrics] = useState<HostMetric[]>([]);
  const [hourly, setHourly] = useState<HostMetricHourly[]>([]);
  const [mwindow, setMwindow] = useState<"24h" | "30d">("24h");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [h, c, m] = await Promise.all([
          getHost(hostId),
          listChecks(hostId),
          getHostMetrics(hostId, 24).catch(() => ({ data: [] as HostMetric[] })),
        ]);
        setHost(h.data);
        setChecks(c.data);
        setMetrics(m.data);
        const res = await Promise.all(c.data.map((ch) => listResults(ch.id, 50)));
        setResults(
          res
            .flatMap((r) => r.data)
            .sort((a, b) => +new Date(b.checked_at) - +new Date(a.checked_at)),
        );
      } catch {
        setError("Hôte introuvable");
      } finally {
        setLoading(false);
      }
    })();
  }, [hostId]);

  // Charge les rollups horaires à la demande (vue 30 jours).
  useEffect(() => {
    if (mwindow === "30d" && hourly.length === 0) {
      getHostMetricsHourly(hostId, 30).then((r) => setHourly(r.data)).catch(() => {});
    }
  }, [mwindow, hostId, hourly.length]);

  const hasMetrics = metrics.length > 0;
  const rawSeries = (field: string) =>
    metrics.map((m) => ({
      label: formatTime(m.collected_at),
      value: Number((m as unknown as Record<string, unknown>)[field] ?? 0),
    }));
  const hourlySeries = (field: string) =>
    hourly.map((m) => ({
      label: new Date(m.bucket).toLocaleString([], { day: "2-digit", month: "2-digit", hour: "2-digit" }),
      value: Number((m as unknown as Record<string, unknown>)[field] ?? 0),
    }));

  // Dernier relevé par disque (C:/D:/...) — uniquement si l'agent en a remonté.
  const latestDisks: Record<string, number> =
    (hasMetrics && metrics[metrics.length - 1].disks) || {};

  const status = useMemo(() => worstStatus(checks.map((c) => c.last_status)), [checks]);
  const checkName = useMemo(() => new Map(checks.map((c) => [c.id, c.name])), [checks]);

  if (loading) return <Loading />;
  if (error || !host) return <ErrorState message={error ?? "Erreur"} />;

  return (
    <div className="space-y-6">
      <Link to="/hosts" className="inline-flex items-center gap-1 text-sm text-ink-soft hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Hosts
      </Link>
      <PageHeader
        title={host.name}
        subtitle={`${host.hostname_or_ip} · ${host.environment}`}
        actions={<StatusBadge status={status} label={undefined} />}
      />

      {/* Résumé */}
      <Card className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Summary icon={Server} label="Hostname / IP" value={host.hostname_or_ip} />
        <Summary icon={Server} label="Environnement" value={host.environment} />
        <Summary icon={Server} label="Uptime" value={uptimeSince(host.created_at)} />
        <Summary icon={Server} label="Checks" value={String(checks.length)} />
        {hasMetrics && metrics[metrics.length - 1].process_count != null && (
          <Summary icon={Server} label="Processus" value={String(metrics[metrics.length - 1].process_count)} />
        )}
        {hasMetrics && metrics[metrics.length - 1].load1 != null && (
          <Summary icon={Server} label="Charge (1 min)" value={String(metrics[metrics.length - 1].load1)} />
        )}
        {hasMetrics && metrics[metrics.length - 1].temperature != null && (
          <Summary icon={Server} label="Température" value={`${metrics[metrics.length - 1].temperature} °C`} />
        )}
      </Card>

      {/* Widgets ressources — uniquement si l'hôte remonte de vraies métriques (agent) */}
      {hasMetrics ? (
        <>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-xs text-ink-faint">
                {mwindow === "24h"
                  ? "Métriques système collectées par agent (24 h, brut)."
                  : "Tendances agrégées par heure (30 jours, downsampling)."}
              </p>
              <div className="flex items-center gap-1 rounded-lg border border-border bg-bg-soft p-1">
                {(["24h", "30d"] as const).map((w) => (
                  <button
                    key={w}
                    onClick={() => setMwindow(w)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${mwindow === w ? "bg-brand text-white" : "text-ink-soft hover:text-ink"}`}
                  >
                    {w === "24h" ? "24 h" : "30 j"}
                  </button>
                ))}
              </div>
            </div>
            <MotionGrid className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {WIDGETS.map((w) => {
                const series = mwindow === "24h" ? rawSeries(w.field) : hourlySeries(w.hourly);
                const last = series.length ? series[series.length - 1].value : 0;
                const Icon = w.icon;
                const st = w.unit === "%" ? metricStatus(last) : "OK";
                return (
                  <Card key={w.key}>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="flex items-center gap-2 text-sm font-medium text-ink-soft">
                        <Icon className="h-4 w-4" /> {w.key}
                      </span>
                      <StatusBadge status={st} label={`${last}${w.unit}`} size="xs" />
                    </div>
                    <MetricArea id={w.key} data={series} color={w.color} unit={w.unit} height={120} />
                  </Card>
                );
              })}
            </MotionGrid>
          </div>

          {/* Détail par disque */}
          {Object.keys(latestDisks).length > 0 && (
            <Card>
              <SectionTitle title={`Disques (${Object.keys(latestDisks).length})`} icon={HardDrive} />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(latestDisks).map(([name, pct]) => (
                  <DiskBar key={name} name={name} pct={pct} />
                ))}
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card className="flex items-center gap-3 text-sm text-ink-soft">
          <Server className="h-5 w-5 shrink-0 text-ink-faint" />
          <span>
            Pas de métriques système pour cet hôte. C'est normal pour un équipement réseau
            (box, routeur, imprimante…) qui n'exécute pas d'agent. Pour suivre CPU/RAM/disque,
            lancez l'agent (<span className="font-mono text-xs">scripts/agent_example.py</span>)
            sur une machine. La supervision se fait ici via les checks ci-dessous.
          </span>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Checks */}
        <Card>
          <SectionTitle title={`Checks (${checks.length})`} />
          <div className="space-y-2">
            {checks.map((c) => (
              <Link
                key={c.id}
                to={`/checks/${c.id}`}
                className="flex items-center justify-between rounded-lg border border-border bg-bg-soft/50 px-3 py-2 transition hover:border-ink-faint/60"
              >
                <div>
                  <p className="text-sm font-medium text-ink">{c.name}</p>
                  <p className="text-xs text-ink-faint">{c.type} · {c.interval_seconds}s</p>
                </div>
                <StatusBadge status={c.last_status} size="xs" />
              </Link>
            ))}
          </div>
        </Card>

        {/* Timeline des événements */}
        <Card>
          <SectionTitle title="Timeline des événements" />
          <div className="relative max-h-[360px] space-y-3 overflow-y-auto border-l border-border pl-4">
            {results.slice(0, 40).map((r) => (
              <div key={r.id} className="relative">
                <span className="absolute -left-[22px] top-1 h-2.5 w-2.5 rounded-full ring-2 ring-bg"
                  style={{ background: r.status === "OK" ? "#10B981" : r.status === "WARNING" ? "#F59E0B" : r.status === "CRITICAL" ? "#EF4444" : "#64748B" }} />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink">{checkName.get(r.check_id) ?? `check #${r.check_id}`}</span>
                  <span className="text-xs text-ink-faint" title={formatDate(r.checked_at)}>{formatTime(r.checked_at)}</span>
                </div>
                {r.message && <p className="text-xs text-ink-soft">{r.message}</p>}
              </div>
            ))}
            {results.length === 0 && <p className="text-sm text-ink-faint">Aucun événement.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}

function DiskBar({ name, pct }: { name: string; pct: number }) {
  const meta = statusMeta(metricStatus(pct));
  return (
    <div className="rounded-lg border border-border bg-bg-soft/50 p-3">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 font-medium text-ink">
          <HardDrive className="h-4 w-4 text-ink-soft" /> {name}
        </span>
        <span className={meta.text}>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-bg">
        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, pct)}%`, background: meta.color }} />
      </div>
    </div>
  );
}

function Summary({ icon: Icon, label, value }: { icon: typeof Server; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="rounded-lg bg-bg-soft p-2 text-ink-soft">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
        <p className="truncate text-sm font-medium text-ink">{value}</p>
      </div>
    </div>
  );
}
