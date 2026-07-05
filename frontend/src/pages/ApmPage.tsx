import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Gauge, Timer, Boxes, RefreshCw } from "lucide-react";
import { listApmApps, getApmSeries, type ApmApp, type ApmPoint } from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { MetricArea } from "../components/charts/MetricArea";
import { EmptyState, Loading } from "../components/States";
import { timeAgo } from "../lib/format";
import { cn } from "../lib/cn";

function health(app: ApmApp): { color: string; label: string } {
  if (app.requests === 0) return { color: "#64748B", label: "Silencieux" };
  if (app.error_rate >= 10) return { color: "#EF4444", label: "Dégradé" };
  if (app.error_rate >= 5 || (app.latency_ms ?? 0) >= 1000) return { color: "#F59E0B", label: "À surveiller" };
  return { color: "#10B981", label: "Sain" };
}

export default function ApmPage() {
  const [apps, setApps] = useState<ApmApp[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [series, setSeries] = useState<ApmPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    const { data } = await listApmApps(15);
    setApps(data);
    if (!selected && data.length) setSelected(data[0].app_name);
  };
  useEffect(() => {
    load().finally(() => setLoading(false));
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selected) return;
    getApmSeries(selected, 24, 48).then((r) => setSeries(r.data));
  }, [selected, apps]);

  const refresh = async () => {
    setRefreshing(true);
    await load().finally(() => setRefreshing(false));
  };

  const chart = useMemo(() => {
    const fmt = (iso: string) =>
      new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    return {
      rpm: series.map((p) => ({ label: fmt(p.t), value: p.rpm })),
      err: series.map((p) => ({ label: fmt(p.t), value: p.error_rate })),
      lat: series.map((p) => ({ label: fmt(p.t), value: p.latency_ms ?? 0 })),
    };
  }, [series]);

  if (loading) return <Loading />;

  const sel = apps.find((a) => a.app_name === selected);

  return (
    <div className="space-y-6">
      <PageHeader
        title="APM"
        subtitle="Supervision applicative — débit, erreurs et latence des applications"
        actions={
          <button onClick={refresh} className="btn-ghost" disabled={refreshing}>
            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} /> Actualiser
          </button>
        }
      />

      {apps.length === 0 ? (
        <Card>
          <EmptyState message="Aucune application instrumentée." />
          <div className="mx-auto max-w-2xl pb-4 text-xs text-ink-faint">
            <p className="mb-2">Envoyez des métriques depuis vos applications (toutes les 30-60 s) :</p>
            <pre className="overflow-x-auto rounded-lg border border-border bg-bg-soft p-3">
{`POST /api/apm/ingest
{"app_name": "mon-erp", "requests": 420, "errors": 3, "latency_ms": 185}`}
            </pre>
            <p className="mt-2">Le backend Opsora s'auto-instrumente : ses métriques apparaîtront ici d'elles-mêmes.</p>
          </div>
        </Card>
      ) : (
        <>
          {/* Cartes applications */}
          <MotionGrid className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {apps.map((a) => {
              const h = health(a);
              const active = a.app_name === selected;
              return (
                <motion.button
                  key={a.app_name}
                  variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
                  onClick={() => setSelected(a.app_name)}
                  className={cn(
                    "card p-4 text-left transition-all hover:-translate-y-0.5",
                    active && "ring-2 ring-brand",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <Boxes className="h-4 w-4 shrink-0 text-ink-faint" />
                      <p className="truncate font-semibold text-ink">{a.app_name}</p>
                    </div>
                    <span className="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold" style={{ background: `${h.color}1f`, color: h.color }}>
                      {h.label}
                    </span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                    <Kpi label="req/min" value={a.rpm} color="#3B82F6" />
                    <Kpi label="erreurs" value={`${a.error_rate}%`} color={a.error_rate >= 5 ? "#EF4444" : "#10B981"} />
                    <Kpi label="latence" value={a.latency_ms != null ? `${a.latency_ms} ms` : "—"} color={(a.latency_ms ?? 0) >= 1000 ? "#F59E0B" : "#8B5CF6"} />
                  </div>
                  {a.last_seen && (
                    <p className="mt-2 text-right text-[11px] text-ink-faint">vu {timeAgo(a.last_seen)}</p>
                  )}
                </motion.button>
              );
            })}
          </MotionGrid>

          {/* Détail : séries 24 h */}
          {sel && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card>
                <SectionTitle title={`Débit — ${sel.app_name}`} icon={Activity} />
                <MetricArea id="apm-rpm" data={chart.rpm} color="#3B82F6" unit="" height={190} />
              </Card>
              <Card>
                <SectionTitle title="Taux d'erreur (%)" icon={AlertTriangle} />
                <MetricArea id="apm-err" data={chart.err} color="#EF4444" unit="%" height={190} domain={[0, 100]} />
              </Card>
              <Card>
                <SectionTitle title="Latence (ms)" icon={Timer} />
                <MetricArea id="apm-lat" data={chart.lat} color="#8B5CF6" unit="" height={190} />
              </Card>
            </div>
          )}

          <p className="flex items-center gap-1.5 text-xs text-ink-faint">
            <Gauge className="h-3.5 w-3.5" />
            Pour alerter sur une application : créez un check de type <code className="rounded bg-bg-soft px-1">apm</code> avec
            <code className="rounded bg-bg-soft px-1">{'{"app": "nom", "metric": "error_rate"}'}</code> et vos seuils.
          </p>
        </>
      )}
    </div>
  );
}

function Kpi({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded-lg bg-bg-soft/60 py-2">
      <p className="text-sm font-bold tabular-nums" style={{ color }}>{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-ink-faint">{label}</p>
    </div>
  );
}
