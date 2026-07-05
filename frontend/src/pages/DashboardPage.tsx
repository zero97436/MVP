import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Server,
  ServerOff,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Gauge,
  ArrowRight,
  Activity,
  SlidersHorizontal,
  Save,
  RotateCcw,
  X,
  Eye,
  EyeOff,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import {
  getIncidents,
  getSummary,
  listChecks,
  listHosts,
  listResults,
  getDashboardLayout,
  saveDashboardLayout,
  resetDashboardLayout,
  type LayoutSection,
} from "../api/endpoints";
import type { Check, CheckResult, CheckStatus, DashboardSummary, Host, Incident } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { HealthCard } from "../components/ui/HostCard";
import { AlertCard } from "../components/ui/AlertCard";
import { LiveEventFeed } from "../components/live/LiveEventFeed";
import { AiSummaryCard } from "../components/ai/AiSummaryCard";
import { AvailabilityChart } from "../components/charts/AvailabilityChart";
import { StatusDonut } from "../components/charts/StatusDonut";
import { ErrorState, SkeletonGrid } from "../components/States";
import { buildHostViews } from "../lib/fleet";
import { statusMeta } from "../lib/status";
import { availabilityBuckets, availabilityRatio } from "../lib/series";
import { formatPercent } from "../lib/format";
import { cn } from "../lib/cn";

const DAY = 24 * 3600 * 1000;
const SEV: Record<CheckStatus, number> = { CRITICAL: 0, WARNING: 1, UNKNOWN: 2, OK: 3 };

const DEFAULT_LAYOUT: LayoutSection[] = [
  { id: "hero", visible: true },
  { id: "kpi", visible: true },
  { id: "incidents", visible: true },
  { id: "trend", visible: true },
  { id: "fleet", visible: true },
];
const SECTION_TITLE: Record<string, string> = {
  hero: "État global & disponibilité",
  kpi: "Compteurs",
  incidents: "Incidents, répartition & live",
  trend: "Tendance & résumé IA",
  fleet: "Flotte (Health Overview)",
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard personnalisable : ordre + visibilité des sections (par utilisateur).
  const [layout, setLayout] = useState<LayoutSection[]>(DEFAULT_LAYOUT);
  const [customize, setCustomize] = useState(false);
  const [savedLayout, setSavedLayout] = useState<LayoutSection[]>(DEFAULT_LAYOUT);

  useEffect(() => {
    (async () => {
      try {
        const [s, i, h, c, l] = await Promise.all([
          getSummary(),
          getIncidents(),
          listHosts(),
          listChecks(),
          getDashboardLayout().catch(() => ({ data: { sections: DEFAULT_LAYOUT, custom: false } })),
        ]);
        setLayout(l.data.sections);
        setSavedLayout(l.data.sections);
        setSummary(s.data);
        setIncidents(i.data);
        setHosts(h.data);
        setChecks(c.data);
        const sample = c.data.slice(0, 24);
        const res = await Promise.all(sample.map((ch) => listResults(ch.id, 200)));
        setResults(res.flatMap((r) => r.data));
      } catch {
        setError("Impossible de charger le dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const hostViews = useMemo(() => buildHostViews(hosts, checks), [hosts, checks]);
  const hostsOnline = hostViews.filter((h) => h.status === "OK").length;
  const hostsOffline = hostViews.length - hostsOnline;
  const availability = useMemo(() => availabilityRatio(results), [results]);
  const avail24h = useMemo(() => availabilityBuckets(results, DAY, 24), [results]);

  if (loading) return <SkeletonGrid count={6} />;
  if (error) return <ErrorState message={error} />;
  if (!summary) return null;

  const c = summary.status_counts;
  const overall: CheckStatus =
    (c.CRITICAL ?? 0) > 0 ? "CRITICAL"
    : (c.WARNING ?? 0) > 0 ? "WARNING"
    : (c.OK ?? 0) === 0 ? "UNKNOWN"
    : "OK";
  const meta = statusMeta(overall);
  const headline =
    overall === "CRITICAL" ? "Intervention requise"
    : overall === "WARNING" ? "Points à surveiller"
    : overall === "UNKNOWN" ? "En attente de données"
    : "Tous les systèmes opérationnels";
  const subline =
    overall === "CRITICAL" ? `${c.CRITICAL} service(s) critiques · ${incidents.length} incident(s) actif(s)`
    : overall === "WARNING" ? `${c.WARNING} avertissement(s) en cours`
    : overall === "UNKNOWN" ? "Aucun résultat de check récent"
    : "Aucun incident actif — rien à signaler";

  const sortedIncidents = [...incidents].sort(
    (a, b) =>
      SEV[a.status] - SEV[b.status] ||
      Number(a.acknowledged) - Number(b.acknowledged) ||
      +new Date(b.since) - +new Date(a.since),
  );
  const sortedHosts = [...hostViews].sort((a, b) => SEV[a.status] - SEV[b.status]);

  const move = (idx: number, dir: -1 | 1) => {
    const next = [...layout];
    const j = idx + dir;
    if (j < 0 || j >= next.length) return;
    [next[idx], next[j]] = [next[j], next[idx]];
    setLayout(next);
  };
  const toggle = (idx: number) => {
    const next = [...layout];
    next[idx] = { ...next[idx], visible: !next[idx].visible };
    setLayout(next);
  };
  const saveLayout = async () => {
    try {
      await saveDashboardLayout(layout);
      setSavedLayout(layout);
      setCustomize(false);
    } catch (e: unknown) {
      if ((e as { response?: { status?: number } })?.response?.status === 403) {
        alert("Dashboards personnalisables : disponibles à partir du plan Professional.");
        cancelLayout();
      }
    }
  };
  const cancelLayout = () => {
    setLayout(savedLayout);
    setCustomize(false);
  };
  const resetLayout = async () => {
    await resetDashboardLayout();
    setLayout(DEFAULT_LAYOUT);
    setSavedLayout(DEFAULT_LAYOUT);
  };

  const SECTIONS: Record<string, ReactNode> = {
    hero: (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 gap-4 lg:grid-cols-3"
      >
        {/* État global — grande carte colorée */}
        <div
          className="card relative overflow-hidden p-6 lg:col-span-2"
          style={{ background: `linear-gradient(135deg, ${meta.color}14, transparent 60%)` }}
        >
          <div className="flex items-start gap-4">
            <span
              className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl"
              style={{ backgroundColor: `${meta.color}22`, color: meta.color }}
            >
              <meta.icon className="h-7 w-7" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={cn("h-2.5 w-2.5 rounded-full", overall !== "OK" && "animate-pulse")} style={{ background: meta.color }} />
                <span className="text-xs font-medium uppercase tracking-wide" style={{ color: meta.color }}>
                  {meta.label}
                </span>
              </div>
              <h2 className="mt-1 text-2xl font-bold text-ink">{headline}</h2>
              <p className="mt-0.5 text-sm text-ink-soft">{subline}</p>
            </div>
            {incidents.length > 0 && (
              <Link to="/incidents" className="btn-primary shrink-0 px-3 py-2 text-xs">
                Traiter <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>

          {/* mini-stats en pied de hero */}
          <div className="mt-5 grid grid-cols-4 gap-3 border-t border-border pt-4">
            <HeroStat label="Hôtes" value={summary.hosts_total} />
            <HeroStat label="Checks" value={summary.checks_total} />
            <HeroStat label="Incidents" value={incidents.length} accent={incidents.length ? meta.color : undefined} />
            <HeroStat label="Dispo 24 h" value={formatPercent(availability, 1)} />
          </div>
        </div>

        {/* Disponibilité en très gros + jauge */}
        <div className="card flex flex-col justify-between p-6">
          <SectionTitle title="Disponibilité" icon={Gauge} />
          <div className="flex flex-1 flex-col items-center justify-center py-2">
            <span
              className="text-5xl font-bold tabular-nums"
              style={{ color: availability >= 99 ? "#10B981" : availability >= 95 ? "#F59E0B" : "#EF4444" }}
            >
              {formatPercent(availability, 1)}
            </span>
            <span className="mt-1 text-xs text-ink-faint">sur les dernières 24 h</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-soft">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(100, availability)}%`,
                background: availability >= 99 ? "#10B981" : availability >= 95 ? "#F59E0B" : "#EF4444",
              }}
            />
          </div>
        </div>
      </motion.div>
    ),
    kpi: (
      <MotionGrid className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <Kpi label="Hôtes UP" value={hostsOnline} tone="ok" icon={Server} />
        <Kpi label="Hôtes DOWN" value={hostsOffline} tone={hostsOffline ? "critical" : "muted"} icon={ServerOff} />
        <Kpi label="OK" value={c.OK ?? 0} tone="ok" icon={CheckCircle2} />
        <Kpi label="Warning" value={c.WARNING ?? 0} tone={(c.WARNING ?? 0) ? "warning" : "muted"} icon={AlertTriangle} />
        <Kpi label="Critical" value={c.CRITICAL ?? 0} tone={(c.CRITICAL ?? 0) ? "critical" : "muted"} icon={XCircle} />
        <Kpi label="Unknown" value={c.UNKNOWN ?? 0} tone="muted" icon={HelpCircle} />
      </MotionGrid>
    ),
    incidents: (
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Incidents — colonne large, priorité de lecture */}
        <Card className="lg:col-span-2">
          <SectionTitle
            title={`Incidents actifs (${incidents.length})`}
            icon={AlertTriangle}
            action={incidents.length > 6 ? (
              <Link to="/incidents" className="text-xs text-brand hover:underline">Voir tout →</Link>
            ) : undefined}
          />
          {incidents.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <CheckCircle2 className="h-10 w-10 text-status-ok" />
              <p className="text-sm font-medium text-status-ok">Tout est sous contrôle 🎉</p>
              <p className="text-xs text-ink-faint">Aucun incident actif en ce moment.</p>
            </div>
          ) : (
            <MotionGrid className="grid grid-cols-1 gap-3">
              {sortedIncidents.slice(0, 6).map((inc) => (
                <AlertCard key={inc.alert_id} incident={inc} acknowledged={inc.acknowledged} />
              ))}
            </MotionGrid>
          )}
        </Card>

        {/* Colonne droite : donut + live */}
        <div className="flex flex-col gap-5">
          <Card>
            <SectionTitle title="Répartition des états" />
            <StatusDonut counts={c} />
          </Card>
          <Card>
            <LiveEventFeed height={220} />
          </Card>
        </div>
      </div>
    ),
    trend: (
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionTitle title="Tendance de disponibilité — 24 h" icon={Activity} />
          <AvailabilityChart data={avail24h} />
        </Card>
        <div className="lg:col-span-1">
          <AiSummaryCard />
        </div>
      </div>
    ),
    fleet: (
      <Card>
        <SectionTitle title={`Health Overview — ${hostViews.length} hôtes`} icon={Server} />
        {hostViews.length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-faint">Aucun hôte enregistré.</p>
        ) : (
          <MotionGrid className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {sortedHosts.map((h) => (
              <HealthCard key={h.id} host={h} />
            ))}
          </MotionGrid>
        )}
      </Card>
    ),
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Dashboard"
        subtitle="Vue d'ensemble temps réel"
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge status={overall} label={meta.label} />
            {!customize ? (
              <button onClick={() => setCustomize(true)} className="btn-ghost" title="Réorganiser / masquer les sections">
                <SlidersHorizontal className="h-4 w-4" /> Personnaliser
              </button>
            ) : (
              <>
                <button onClick={resetLayout} className="btn-ghost text-ink-faint" title="Revenir au dashboard par défaut">
                  <RotateCcw className="h-4 w-4" /> Défaut
                </button>
                <button onClick={cancelLayout} className="btn-ghost">
                  <X className="h-4 w-4" /> Annuler
                </button>
                <button onClick={saveLayout} className="btn-primary">
                  <Save className="h-4 w-4" /> Enregistrer
                </button>
              </>
            )}
          </div>
        }
      />

      {layout.map((s, i) => {
        const node = SECTIONS[s.id];
        if (!node) return null;
        if (!customize) return s.visible ? <div key={s.id}>{node}</div> : null;
        return (
          <div
            key={s.id}
            className={cn(
              "relative rounded-2xl border border-dashed border-border p-3 pt-10 transition-opacity",
              !s.visible && "opacity-40",
            )}
          >
            <div className="absolute left-3 right-3 top-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                {SECTION_TITLE[s.id] ?? s.id}
              </span>
              <div className="flex items-center gap-1">
                <button onClick={() => move(i, -1)} disabled={i === 0} className="btn-ghost px-2 py-1 disabled:opacity-30" title="Monter">
                  <ChevronUp className="h-4 w-4" />
                </button>
                <button onClick={() => move(i, 1)} disabled={i === layout.length - 1} className="btn-ghost px-2 py-1 disabled:opacity-30" title="Descendre">
                  <ChevronDown className="h-4 w-4" />
                </button>
                <button onClick={() => toggle(i)} className="btn-ghost px-2 py-1" title={s.visible ? "Masquer" : "Afficher"}>
                  {s.visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
              </div>
            </div>
            {node}
          </div>
        );
      })}
    </div>
  );
}

function HeroStat({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="mt-0.5 text-xl font-bold tabular-nums" style={accent ? { color: accent } : undefined}>
        {value}
      </p>
    </div>
  );
}

const TONE: Record<string, { text: string; bg: string; ring: string }> = {
  ok: { text: "text-status-ok", bg: "bg-status-ok/10", ring: "ring-status-ok/20" },
  warning: { text: "text-status-warning", bg: "bg-status-warning/10", ring: "ring-status-warning/20" },
  critical: { text: "text-status-critical", bg: "bg-status-critical/10", ring: "ring-status-critical/20" },
  muted: { text: "text-ink-soft", bg: "bg-bg-soft", ring: "ring-border" },
};

function Kpi({ label, value, tone, icon: Icon }: { label: string; value: number; tone: string; icon: typeof Server }) {
  const t = TONE[tone] ?? TONE.muted;
  return (
    <motion.div
      variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
      className={cn("card flex items-center gap-3 p-3 ring-1 ring-inset", t.ring)}
    >
      <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-lg", t.bg, t.text)}>
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className={cn("text-2xl font-bold leading-none tabular-nums", t.text)}>{value}</p>
        <p className="mt-1 truncate text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
      </div>
    </motion.div>
  );
}
