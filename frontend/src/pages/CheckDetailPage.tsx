import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Play, Timer, Gauge, History } from "lucide-react";
import { getCheck, listResults, runCheck } from "../api/endpoints";
import type { Check, CheckResult } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { MetricCard } from "../components/ui/MetricCard";
import { AvailabilityChart } from "../components/charts/AvailabilityChart";
import { ResponseTimeChart } from "../components/charts/ResponseTimeChart";
import { PerfdataChart } from "../components/charts/PerfdataChart";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { availabilityBuckets, availabilityRatio, responseTimeSeries } from "../lib/series";
import { formatDate, formatMs, formatPercent } from "../lib/format";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

const DAY = 24 * 3600 * 1000;

export default function CheckDetailPage() {
  const { id } = useParams();
  const checkId = Number(id);
  const [check, setCheck] = useState<Check | null>(null);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [perfKey, setPerfKey] = useState<string | null>(null);
  const { user } = useAuth();
  const editable = canEdit(user);

  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const PAGE = 300;

  const load = () => {
    Promise.all([getCheck(checkId), listResults(checkId, PAGE)])
      .then(([c, r]) => {
        setCheck(c.data);
        setResults(r.data);
        setHasMore(r.data.length === PAGE);
      })
      .catch(() => setError("Check introuvable"))
      .finally(() => setLoading(false));
  };
  useEffect(load, [checkId]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const { data } = await listResults(checkId, PAGE, results.length);
      setResults((r) => [...r, ...data]);
      setHasMore(data.length === PAGE);
    } finally {
      setLoadingMore(false);
    }
  };

  const run = async () => {
    setRunning(true);
    await runCheck(checkId);
    load();
    setRunning(false);
  };

  const avail = useMemo(() => availabilityRatio(results), [results]);
  const avail24h = useMemo(() => availabilityBuckets(results, DAY, 24), [results]);
  const rt = useMemo(() => responseTimeSeries(results), [results]);
  const avgMs = useMemo(
    () => (rt.length ? Math.round(rt.reduce((a, r) => a + r.ms, 0) / rt.length) : null),
    [rt],
  );

  // Clés perfdata numériques disponibles dans l'historique.
  const perfKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const r of results) {
      for (const [k, v] of Object.entries(r.perfdata ?? {})) {
        if (typeof v === "number") keys.add(k);
      }
    }
    return [...keys];
  }, [results]);

  const activePerfKey = perfKey && perfKeys.includes(perfKey) ? perfKey : perfKeys[0] ?? null;

  const perfSeries = useMemo(() => {
    if (!activePerfKey) return [];
    return [...results]
      .filter((r) => typeof r.perfdata?.[activePerfKey] === "number")
      .sort((a, b) => +new Date(a.checked_at) - +new Date(b.checked_at))
      .map((r) => ({
        label: new Date(r.checked_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        value: r.perfdata[activePerfKey] as number,
      }));
  }, [results, activePerfKey]);

  if (loading) return <Loading />;
  if (error || !check) return <ErrorState message={error ?? "Erreur"} />;

  return (
    <div className="space-y-6">
      <Link to="/checks" className="inline-flex items-center gap-1 text-sm text-ink-soft hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Checks
      </Link>
      <PageHeader
        title={check.name}
        subtitle={`${check.type} · intervalle ${check.interval_seconds}s · timeout ${check.timeout_seconds}s`}
        actions={
          editable && (
            <button onClick={run} disabled={running} className="btn-primary">
              <Play className="h-4 w-4" /> {running ? "Exécution..." : "Exécuter"}
            </button>
          )
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Statut actuel" value={check.last_status ?? "UNKNOWN"} icon={Gauge}
          accent={check.last_status === "OK" ? "ok" : check.last_status === "WARNING" ? "warning" : check.last_status === "CRITICAL" ? "critical" : "unknown"} />
        <MetricCard label="Disponibilité" value={formatPercent(avail, 1)} icon={Gauge} accent={avail >= 99 ? "ok" : avail >= 95 ? "warning" : "critical"} />
        <MetricCard label="Temps moyen" value={formatMs(avgMs)} icon={Timer} accent="info" />
        <MetricCard label="Résultats" value={results.length} icon={History} accent="neutral" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle title="Disponibilité — 24 h" icon={Gauge} />
          <AvailabilityChart data={avail24h} />
        </Card>
        <Card>
          <SectionTitle title="Temps de réponse" icon={Timer} />
          {rt.length ? <ResponseTimeChart data={rt} /> : (
            <p className="flex h-[220px] items-center justify-center text-sm text-ink-faint">Aucune mesure de durée disponible.</p>
          )}
        </Card>
      </div>

      {perfKeys.length > 0 && (
        <Card>
          <SectionTitle
            title="Perfdata"
            icon={Gauge}
            action={
              <select
                value={activePerfKey ?? ""}
                onChange={(e) => setPerfKey(e.target.value)}
                className="input py-1.5 text-xs"
              >
                {perfKeys.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
            }
          />
          {activePerfKey && <PerfdataChart data={perfSeries} name={activePerfKey} />}
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        <div className="p-5 pb-0"><SectionTitle title="Historique des résultats" icon={History} /></div>
        {results.length === 0 ? (
          <div className="p-5"><EmptyState message="Aucun résultat encore." /></div>
        ) : (
          <>
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-bg-soft/50 text-left text-xs uppercase tracking-wide text-ink-faint">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Valeur</th>
                <th className="px-4 py-3">Message</th>
                <th className="px-4 py-3">Durée</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.id} className="border-t border-border">
                  <td className="px-4 py-2.5 text-ink-faint">{formatDate(r.checked_at)}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={r.status} size="xs" /></td>
                  <td className="px-4 py-2.5 text-ink-soft">{r.value ?? "—"}</td>
                  <td className="px-4 py-2.5 text-ink-soft">{r.message}</td>
                  <td className="px-4 py-2.5 text-ink-faint">{formatMs(r.duration_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {hasMore && (
            <button onClick={loadMore} disabled={loadingMore}
              className="flex w-full items-center justify-center gap-2 border-t border-border py-3 text-sm text-ink-soft hover:text-ink">
              {loadingMore ? "Chargement…" : "Charger plus"}
            </button>
          )}
          </>
        )}
      </Card>
    </div>
  );
}
