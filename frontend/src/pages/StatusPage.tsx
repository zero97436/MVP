import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, RefreshCw } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import { api } from "../api/client";
import { cn } from "../lib/cn";

interface PublicService {
  name: string;
  description: string | null;
  category: string;
  status: "OK" | "WARNING" | "CRITICAL" | "UNKNOWN";
}
interface PublicStatus {
  title: string;
  overall: PublicService["status"];
  services: PublicService[];
  generated_at: string;
}

const META = {
  OK: { color: "#10B981", icon: CheckCircle2, label: "Opérationnel" },
  WARNING: { color: "#F59E0B", icon: AlertTriangle, label: "Dégradé" },
  CRITICAL: { color: "#EF4444", icon: XCircle, label: "Incident en cours" },
  UNKNOWN: { color: "#64748B", icon: HelpCircle, label: "Inconnu" },
} as const;

const BANNER = {
  OK: "Tous les services sont opérationnels",
  WARNING: "Dégradation en cours sur certains services",
  CRITICAL: "Incident en cours",
  UNKNOWN: "État indéterminé",
} as const;

export default function StatusPage() {
  const [data, setData] = useState<PublicStatus | null>(null);
  const [error, setError] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = () =>
    api.get<PublicStatus>("/public/status")
      .then((r) => { setData(r.data); setUpdatedAt(new Date()); setError(false); })
      .catch(() => setError(true));

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const groups = useMemo(() => {
    const map = new Map<string, PublicService[]>();
    for (const s of data?.services ?? []) {
      (map.get(s.category) ?? map.set(s.category, []).get(s.category)!).push(s);
    }
    return [...map.entries()];
  }, [data]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg text-ink-soft">
        Page de statut indisponible.
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <RefreshCw className="h-6 w-6 animate-spin text-ink-faint" />
      </div>
    );
  }

  const meta = META[data.overall];

  return (
    <div className="min-h-screen bg-bg px-4 py-10 text-ink">
      <div className="mx-auto w-full max-w-3xl space-y-6">
        {/* En-tête */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Logo className="h-9 w-9" />
            <h1 className="text-lg font-bold">{data.title}</h1>
          </div>
          {updatedAt && (
            <span className="text-xs text-ink-faint">
              mis à jour à {updatedAt.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
        </div>

        {/* Bannière d'état global */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4 rounded-2xl border p-6"
          style={{ borderColor: `${meta.color}55`, background: `linear-gradient(135deg, ${meta.color}1f, ${meta.color}08)` }}
        >
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl" style={{ background: `${meta.color}26`, color: meta.color }}>
            <meta.icon className="h-6 w-6" />
          </span>
          <div>
            <p className="text-xl font-bold" style={{ color: meta.color }}>{BANNER[data.overall]}</p>
            <p className="text-sm text-ink-soft">
              {data.services.length} service(s) surveillé(s) en continu
            </p>
          </div>
        </motion.div>

        {/* Services par catégorie */}
        {groups.length === 0 ? (
          <p className="py-10 text-center text-sm text-ink-faint">Aucun service publié pour le moment.</p>
        ) : (
          groups.map(([category, services]) => (
            <div key={category} className="card overflow-hidden p-0">
              <p className="border-b border-border bg-bg-soft/50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-ink-soft">
                {category}
              </p>
              <div className="divide-y divide-border">
                {services.map((s) => {
                  const m = META[s.status];
                  return (
                    <div key={s.name} className="flex items-center justify-between gap-3 px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-ink">{s.name}</p>
                        {s.description && <p className="truncate text-xs text-ink-faint">{s.description}</p>}
                      </div>
                      <span className="flex shrink-0 items-center gap-2 text-xs font-medium" style={{ color: m.color }}>
                        <span className={cn("h-2 w-2 rounded-full", s.status !== "OK" && "animate-pulse")} style={{ background: m.color }} />
                        {m.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}

        <p className="pt-4 text-center text-xs text-ink-faint">
          Actualisation automatique toutes les 30 s · propulsé par Opsora
        </p>
      </div>
    </div>
  );
}
