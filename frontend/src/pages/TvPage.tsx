import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, X } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import { getIncidents, getSummary, listChecks, listHosts } from "../api/endpoints";
import type { Check, CheckStatus, DashboardSummary, Host, Incident } from "../types";
import { buildHostViews } from "../lib/fleet";
import { statusMeta } from "../lib/status";
import { useNow } from "../hooks/useNow";
import { timeAgo } from "../lib/format";
import { cn } from "../lib/cn";

const SEV: Record<CheckStatus, number> = { CRITICAL: 0, WARNING: 1, UNKNOWN: 2, OK: 3 };

export default function TvPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const now = useNow(1000);

  useEffect(() => {
    const load = () =>
      Promise.all([getSummary(), getIncidents(), listHosts(), listChecks()])
        .then(([s, i, h, c]) => { setSummary(s.data); setIncidents(i.data); setHosts(h.data); setChecks(c.data); })
        .catch(() => {});
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const views = useMemo(
    () => buildHostViews(hosts, checks).sort((a, b) => SEV[a.status] - SEV[b.status]),
    [hosts, checks],
  );

  if (!summary) {
    return <div className="flex min-h-screen items-center justify-center bg-black text-ink-faint">Chargement…</div>;
  }

  const c = summary.status_counts;
  const overall: CheckStatus =
    (c.CRITICAL ?? 0) > 0 ? "CRITICAL"
    : (c.WARNING ?? 0) > 0 ? "WARNING"
    : (c.OK ?? 0) === 0 ? "UNKNOWN" : "OK";
  const meta = statusMeta(overall);
  const sorted = [...incidents].sort((a, b) => SEV[a.status] - SEV[b.status]);

  return (
    <div className="flex min-h-screen flex-col gap-6 bg-black p-8 text-ink">
      {/* En-tête : titre + horloge géante + sortie */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-ink-soft">
          <Logo className="h-9 w-9" />
          <span className="text-xl font-bold tracking-tight">Opsora</span>
        </div>
        <span className="text-5xl font-bold tabular-nums tracking-tight">
          {now.toLocaleTimeString("fr-FR")}
        </span>
        <Link to="/dashboard" className="rounded-lg border border-border p-2 text-ink-faint hover:text-ink" title="Quitter le mode TV">
          <X className="h-5 w-5" />
        </Link>
      </div>

      {/* Bannière d'état géante */}
      <motion.div
        key={overall}
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center justify-between rounded-3xl border-2 px-10 py-8"
        style={{ borderColor: meta.color, background: `linear-gradient(135deg, ${meta.color}26, ${meta.color}08)` }}
      >
        <div className="flex items-center gap-6">
          <span className={cn("h-6 w-6 rounded-full", overall !== "OK" && "animate-pulse")} style={{ background: meta.color }} />
          <span className="text-5xl font-black" style={{ color: meta.color }}>
            {overall === "OK" ? "TOUT EST OPÉRATIONNEL"
              : overall === "CRITICAL" ? `${c.CRITICAL} CRITIQUE(S)`
              : overall === "WARNING" ? `${c.WARNING} AVERTISSEMENT(S)`
              : "EN ATTENTE DE DONNÉES"}
          </span>
        </div>
        <div className="flex gap-10 text-center">
          <TvStat label="Hôtes" value={summary.hosts_total} />
          <TvStat label="Checks" value={summary.checks_total} />
          <TvStat label="Incidents" value={incidents.length} color={incidents.length ? "#EF4444" : "#10B981"} />
        </div>
      </motion.div>

      <div className="grid flex-1 grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Incidents */}
        <div className="space-y-3">
          <p className="text-sm font-semibold uppercase tracking-widest text-ink-faint">Incidents actifs</p>
          {sorted.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-border">
              <CheckCircle2 className="h-14 w-14 text-status-ok" />
              <p className="text-xl font-semibold text-status-ok">Aucun incident</p>
            </div>
          ) : (
            sorted.slice(0, 6).map((inc) => {
              const m = statusMeta(inc.status);
              return (
                <div key={inc.alert_id} className="flex items-center gap-4 rounded-2xl border-l-8 bg-bg-soft/40 px-5 py-4"
                     style={{ borderColor: m.color }}>
                  <span className={cn("h-3.5 w-3.5 shrink-0 rounded-full animate-pulse")} style={{ background: m.color }} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xl font-semibold">
                      {inc.host_name} <span className="text-ink-faint">/</span> {inc.check_name}
                    </p>
                    {inc.message && <p className="truncate text-sm text-ink-soft">{inc.message}</p>}
                  </div>
                  <span className="shrink-0 text-sm text-ink-faint">{timeAgo(inc.since)}</span>
                </div>
              );
            })
          )}
        </div>

        {/* Flotte */}
        <div className="space-y-3">
          <p className="text-sm font-semibold uppercase tracking-widest text-ink-faint">Flotte — {views.length} hôtes</p>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            {views.slice(0, 12).map((v) => {
              const m = statusMeta(v.status);
              return (
                <div key={v.id} className="rounded-2xl border px-4 py-3"
                     style={{ borderColor: `${m.color}55`, background: `${m.color}12` }}>
                  <div className="flex items-center gap-2">
                    <span className={cn("h-2.5 w-2.5 shrink-0 rounded-full", v.status !== "OK" && "animate-pulse")} style={{ background: m.color }} />
                    <p className="truncate font-semibold">{v.name}</p>
                  </div>
                  <p className="mt-1 text-xs" style={{ color: m.color }}>{m.label} · {v.checksCount} check(s)</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <p className="text-center text-xs text-ink-faint">Mode TV · actualisation 15 s</p>
    </div>
  );
}

function TvStat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div>
      <p className="text-4xl font-bold tabular-nums" style={color ? { color } : undefined}>{value}</p>
      <p className="text-xs uppercase tracking-widest text-ink-faint">{label}</p>
    </div>
  );
}
