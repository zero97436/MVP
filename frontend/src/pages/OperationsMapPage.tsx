import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShoppingCart, Truck, Warehouse, Mail, Banknote, Users, Globe, Server,
  Database, Cloud, Network, Shield, Boxes, Activity, Briefcase,
  AlertTriangle, ArrowUpRight, Move, Save, RotateCcw, X, type LucideIcon,
} from "lucide-react";
import {
  listBam, getSummary, getIncidents, listHosts, listChecks, listResults,
  saveBamLayout, type BamService,
} from "../api/endpoints";
import type { Check, CheckResult, CheckStatus, DashboardSummary, Host, Incident } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Card, SectionTitle } from "../components/ui/Card";
import { AvailabilityChart } from "../components/charts/AvailabilityChart";
import { ErrorState, SkeletonGrid } from "../components/States";
import { statusMeta } from "../lib/status";
import { buildHostViews } from "../lib/fleet";
import { availabilityBuckets } from "../lib/series";
import { formatPercent } from "../lib/format";
import { cn } from "../lib/cn";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

const DAY = 24 * 3600 * 1000;
const TILE_W = 208;
const TILE_H = 130;
const GAP_X = 22;
const GAP_Y = 60;
const PAD = 20;
const COLS = 4;

const ICONS: Record<string, LucideIcon> = {
  cart: ShoppingCart, truck: Truck, warehouse: Warehouse, mail: Mail,
  finance: Banknote, hr: Users, globe: Globe, server: Server, database: Database,
  cloud: Cloud, network: Network, shield: Shield,
};
const LAYER_ORDER = ["Applications métier", "Back-Office", "Infrastructure", "Général"];
type XY = { x: number; y: number };

export default function OperationsMapPage() {
  const { user } = useAuth();
  const editable = canEdit(user);

  const [bam, setBam] = useState<BamService[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [edit, setEdit] = useState(false);
  const [pos, setPos] = useState<Record<number, XY>>({});
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ id: number; dx: number; dy: number } | null>(null);

  const load = async () => {
    const [b, s, i, h, c] = await Promise.all([
      listBam(), getSummary(), getIncidents(), listHosts(), listChecks(),
    ]);
    setBam(b.data);
    setSummary(s.data);
    setIncidents(i.data);
    setHosts(h.data);
    setChecks(c.data);
    const sample = c.data.slice(0, 16);
    const res = await Promise.all(sample.map((ch: Check) => listResults(ch.id, 120)));
    setResults(res.flatMap((r) => r.data));
  };

  useEffect(() => {
    load().catch(() => setError("Impossible de charger la vue opérations")).finally(() => setLoading(false));
  }, []);

  // Placement auto par couche (fallback quand pas de position enregistrée).
  const autoLayout = useMemo<Record<number, XY>>(() => {
    const map = new Map<string, BamService[]>();
    for (const s of bam) {
      const k = s.category || "Général";
      (map.get(k) ?? map.set(k, []).get(k)!).push(s);
    }
    const layers = [...map.entries()].sort(
      (a, b) => (idx(a[0]) - idx(b[0])) || a[0].localeCompare(b[0]),
    );
    const out: Record<number, XY> = {};
    let y = PAD;
    for (const [, services] of layers) {
      services.forEach((s, i) => {
        const col = i % COLS;
        const row = Math.floor(i / COLS);
        out[s.id] = { x: PAD + col * (TILE_W + GAP_X), y: y + row * (TILE_H + GAP_Y) };
      });
      const rows = Math.ceil(services.length / COLS) || 1;
      y += rows * (TILE_H + GAP_Y) + GAP_Y / 2;
    }
    return out;
  }, [bam]);

  // Positions effectives = enregistrées, sinon auto.
  useEffect(() => {
    const p: Record<number, XY> = {};
    for (const s of bam) {
      p[s.id] = s.pos_x != null && s.pos_y != null
        ? { x: s.pos_x, y: s.pos_y }
        : (autoLayout[s.id] ?? { x: PAD, y: PAD });
    }
    setPos(p);
    setDirty(false);
  }, [bam, autoLayout]);

  const canvasHeight = useMemo(() => {
    const maxY = Object.values(pos).reduce((m, p) => Math.max(m, p.y), 0);
    return Math.max(520, maxY + TILE_H + PAD);
  }, [pos]);

  const traffic = useMemo(() => availabilityBuckets(results, DAY, 24), [results]);

  /* ---- drag handlers ---- */
  const onDown = (e: React.PointerEvent, id: number) => {
    if (!edit) return;
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const p = pos[id];
    drag.current = { id, dx: e.clientX - rect.left - p.x, dy: e.clientY - rect.top - p.y };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };
  const onMove = (e: React.PointerEvent) => {
    if (!drag.current) return;
    const rect = canvasRef.current!.getBoundingClientRect();
    const maxX = rect.width - TILE_W - 2;
    const maxY = canvasHeight - TILE_H - 2;
    const x = Math.max(0, Math.min(e.clientX - rect.left - drag.current.dx, maxX));
    const y = Math.max(0, Math.min(e.clientY - rect.top - drag.current.dy, maxY));
    const id = drag.current.id;
    setPos((prev) => ({ ...prev, [id]: { x, y } }));
    setDirty(true);
  };
  const onUp = () => { drag.current = null; };

  const save = async () => {
    setSaving(true);
    try {
      await saveBamLayout(bam.map((s) => ({ id: s.id, pos_x: Math.round(pos[s.id].x), pos_y: Math.round(pos[s.id].y) })));
      await load();
      setEdit(false);
    } finally {
      setSaving(false);
    }
  };
  const reset = async () => {
    setSaving(true);
    try {
      await saveBamLayout(bam.map((s) => ({ id: s.id, pos_x: null, pos_y: null })));
      await load();
    } finally {
      setSaving(false);
    }
  };
  const cancel = () => {
    const p: Record<number, XY> = {};
    for (const s of bam) p[s.id] = s.pos_x != null && s.pos_y != null ? { x: s.pos_x, y: s.pos_y } : autoLayout[s.id];
    setPos(p);
    setDirty(false);
    setEdit(false);
  };

  if (loading) return <SkeletonGrid count={6} />;
  if (error) return <ErrorState message={error} />;
  if (!summary) return null;

  const c = summary.status_counts;
  const okServices = bam.filter((s) => s.status === "OK").length;
  const koServices = bam.filter((s) => s.status === "CRITICAL").length;
  const hostViews = buildHostViews(hosts, checks);
  const hostsUp = hostViews.filter((h) => h.status === "OK").length;
  const svcTotal = (c.OK ?? 0) + (c.WARNING ?? 0) + (c.CRITICAL ?? 0) + (c.UNKNOWN ?? 0);
  const checksHealth = svcTotal ? ((c.OK ?? 0) / svcTotal) * 100 : 100;

  const overall: CheckStatus =
    koServices > 0 ? "CRITICAL"
    : bam.some((s) => s.status === "WARNING") ? "WARNING"
    : bam.length === 0 ? "UNKNOWN"
    : "OK";
  const meta = statusMeta(overall);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vue Opérations"
        subtitle="Cartographie métier temps réel — glissez les tuiles pour composer votre carte"
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge status={overall} label={meta.label} />
            {editable && bam.length > 0 && !edit && (
              <button onClick={() => setEdit(true)} className="btn-ghost">
                <Move className="h-4 w-4" /> Réorganiser
              </button>
            )}
            {edit && (
              <>
                <button onClick={reset} disabled={saving} className="btn-ghost text-ink-faint" title="Revenir au placement automatique par couche">
                  <RotateCcw className="h-4 w-4" /> Auto
                </button>
                <button onClick={cancel} disabled={saving} className="btn-ghost">
                  <X className="h-4 w-4" /> Annuler
                </button>
                <button onClick={save} disabled={saving || !dirty} className="btn-primary">
                  <Save className="h-4 w-4" /> {saving ? "…" : "Enregistrer"}
                </button>
              </>
            )}
          </div>
        }
      />

      {/* KPI */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiTile label="Services métier OK" value={`${okServices}/${bam.length}`} icon={Briefcase} tone={koServices ? "critical" : "ok"} />
        <KpiTile label="Santé des checks" value={formatPercent(checksHealth, 1)} icon={Activity} tone={checksHealth >= 99 ? "ok" : checksHealth >= 95 ? "warning" : "critical"} />
        <KpiTile label="Hôtes en ligne" value={`${hostsUp}/${hosts.length}`} icon={Server} tone={hostsUp === hosts.length ? "ok" : "warning"} />
        <KpiTile label="Incidents actifs" value={incidents.length} icon={AlertTriangle} tone={incidents.length ? "critical" : "ok"} />
      </div>

      {/* Carte */}
      <div className="card overflow-hidden p-0">
        <div className="relative flex items-center justify-between px-6 py-4" style={{ background: `linear-gradient(120deg, ${meta.color}22, transparent 70%)` }}>
          <div>
            <h2 className="text-xl font-black tracking-tight" style={{ color: meta.color }}>OPÉRATIONS GLOBALES</h2>
            <p className="text-xs uppercase tracking-[0.2em] text-ink-faint">
              {summary.hosts_total} hôtes · {svcTotal} services · {bam.length} services métier
            </p>
          </div>
          {edit
            ? <span className="rounded-full bg-brand/15 px-3 py-1.5 text-xs font-medium text-brand">✋ Mode édition — glissez les tuiles</span>
            : <span className="hidden items-center gap-2 rounded-full bg-bg-soft px-3 py-1.5 text-xs text-ink-soft sm:flex">
                <span className={cn("h-2 w-2 rounded-full", overall !== "OK" && "animate-pulse")} style={{ background: meta.color }} /> temps réel
              </span>}
        </div>

        {bam.length === 0 ? (
          <EmptyMap />
        ) : (
          <div className="overflow-x-auto">
            <div
              ref={canvasRef}
              onPointerMove={onMove}
              onPointerUp={onUp}
              onPointerLeave={onUp}
              className={cn("relative mx-auto", edit && "select-none")}
              style={{
                height: canvasHeight,
                minWidth: PAD * 2 + COLS * TILE_W + (COLS - 1) * GAP_X,
                backgroundImage: edit
                  ? "radial-gradient(circle, rgba(148,163,184,0.16) 1px, transparent 1px)"
                  : undefined,
                backgroundSize: edit ? "22px 22px" : undefined,
              }}
            >
              {bam.map((s) => {
                const p = pos[s.id] ?? { x: PAD, y: PAD };
                return (
                  <div
                    key={s.id}
                    onPointerDown={(e) => onDown(e, s.id)}
                    className={cn("absolute", edit ? "cursor-move touch-none" : "")}
                    style={{ left: p.x, top: p.y, width: TILE_W }}
                  >
                    <ServiceTile svc={s} interactive={!edit} />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <Card>
        <SectionTitle title="Tendance de disponibilité — 24 h" icon={Activity} />
        <AvailabilityChart data={traffic} height={200} />
      </Card>
    </div>
  );
}

function idx(layer: string): number {
  const i = LAYER_ORDER.indexOf(layer);
  return i === -1 ? LAYER_ORDER.length : i;
}

/* ---------- Tuile ---------- */
function ServiceTile({ svc, interactive }: { svc: BamService; interactive: boolean }) {
  const meta = statusMeta(svc.status);
  const Icon = (svc.icon && ICONS[svc.icon]) || Boxes;
  const ratio = svc.total ? (svc.ok_count / svc.total) * 100 : 0;

  const inner = (
    <>
      {interactive && <ArrowUpRight className="absolute right-2.5 top-2.5 h-3.5 w-3.5 text-ink-faint opacity-0 transition-opacity group-hover:opacity-100" />}
      <div className="flex items-start gap-3">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg" style={{ background: `${meta.color}26`, color: meta.color }}>
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-ink">{svc.name}</p>
          <div className="mt-0.5 flex items-center gap-1.5">
            <span className={cn("h-2 w-2 rounded-full", svc.status !== "OK" && "animate-pulse")} style={{ background: meta.color }} />
            <span className="text-xs font-medium" style={{ color: meta.color }}>{meta.label}</span>
          </div>
        </div>
      </div>
      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-[11px] text-ink-faint">
          <span>{svc.ok_count}/{svc.total} composants OK</span>
          <span className="tabular-nums">{formatPercent(ratio, 0)}</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-black/30">
          <div className="h-full rounded-full transition-all" style={{ width: `${ratio}%`, background: meta.color }} />
        </div>
      </div>
    </>
  );

  const cls = "group relative block overflow-hidden rounded-xl border p-4";
  const style = { borderColor: `${meta.color}55`, background: `linear-gradient(135deg, ${meta.color}1f, ${meta.color}0a)` };

  if (!interactive) {
    return <div className={cn(cls, "shadow-md")} style={style}>{inner}</div>;
  }
  return (
    <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.25 }}>
      <Link to="/bam" className={cn(cls, "transition-all hover:-translate-y-0.5 hover:shadow-lg")} style={style}>{inner}</Link>
    </motion.div>
  );
}

/* ---------- KPI ---------- */
const TONE: Record<string, string> = { ok: "#10B981", warning: "#F59E0B", critical: "#EF4444" };
function KpiTile({ label, value, icon: Icon, tone }: { label: string; value: string | number; icon: LucideIcon; tone: string }) {
  const color = TONE[tone] ?? "#64748B";
  return (
    <div className="card flex items-center gap-3 p-4">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg" style={{ background: `${color}1f`, color }}>
        <Icon className="h-5 w-5" />
      </span>
      <div className="min-w-0">
        <p className="text-2xl font-bold leading-none tabular-nums" style={{ color }}>{value}</p>
        <p className="mt-1 truncate text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
      </div>
    </div>
  );
}

function EmptyMap() {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-16 text-center">
      <Boxes className="h-12 w-12 text-ink-faint" />
      <p className="text-sm font-medium text-ink">Aucun service métier défini</p>
      <p className="max-w-md text-xs text-ink-faint">
        Créez vos services métier et rangez-les par couche. Ils s'afficheront ici en tuiles que vous
        pourrez librement positionner.
      </p>
      <Link to="/bam" className="btn-primary mt-1 px-4 py-2 text-sm">
        <Briefcase className="h-4 w-4" /> Configurer les services métier
      </Link>
    </div>
  );
}
