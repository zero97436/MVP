import { useMemo, useState } from "react";
import { Search, Filter, BellRing } from "lucide-react";
import { ackIncident, analyzeIncident, createTicket, getAgentCommand, getIncidents, remediateIncident, unackIncident } from "../api/endpoints";
import { useNavigate } from "react-router-dom";
import type { AnalysisState, RemediationState } from "../components/ui/AlertCard";
import type { CheckStatus } from "../types";
import { usePolling } from "../hooks/usePolling";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, MotionGrid } from "../components/ui/Card";
import { AlertCard } from "../components/ui/AlertCard";
import { MetricCard } from "../components/ui/MetricCard";
import { ErrorState, Loading } from "../components/States";
import { MaintenancePanel } from "../components/MaintenancePanel";
import { cn } from "../lib/cn";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

const FILTERS: (CheckStatus | "ALL")[] = ["ALL", "CRITICAL", "WARNING", "UNKNOWN"];

export default function IncidentCenterPage() {
  const { data: incidents, error, loading, refresh } = usePolling(
    () => getIncidents().then((r) => r.data),
    10000,
  );
  const [filter, setFilter] = useState<CheckStatus | "ALL">("ALL");
  const [q, setQ] = useState("");
  const { user } = useAuth();
  const editable = canEdit(user);
  const navigate = useNavigate();

  const [ticketBusy, setTicketBusy] = useState<number | null>(null);
  const openTicket = async (alertId: number) => {
    setTicketBusy(alertId);
    try {
      await createTicket({ alert_id: alertId });
      navigate("/tickets");
    } finally {
      setTicketBusy(null);
    }
  };

  const list = incidents ?? [];
  const counts = useMemo(() => {
    const c: Record<string, number> = { CRITICAL: 0, WARNING: 0, UNKNOWN: 0 };
    for (const i of list) c[i.status] = (c[i.status] ?? 0) + 1;
    return c;
  }, [list]);
  const ackedCount = list.filter((i) => i.acknowledged).length;

  const filtered = list.filter((i) => {
    if (filter !== "ALL" && i.status !== filter) return false;
    const hay = `${i.host_name} ${i.check_name} ${i.message ?? ""}`.toLowerCase();
    return hay.includes(q.toLowerCase());
  });

  const toggleAck = async (id: number, acknowledged: boolean) => {
    await (acknowledged ? unackIncident(id) : ackIncident(id));
    refresh();
  };

  const [analyses, setAnalyses] = useState<Record<number, AnalysisState>>({});
  const analyze = async (id: number) => {
    setAnalyses((p) => ({ ...p, [id]: { loading: true } }));
    try {
      const { data } = await analyzeIncident(id);
      setAnalyses((p) => ({
        ...p,
        [id]: {
          loading: false,
          text: data.analysis,
          suggested: data.suggested_action,
          actions: data.available_actions,
        },
      }));
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Analyse impossible (IA injoignable ?).";
      setAnalyses((p) => ({ ...p, [id]: { loading: false, error: detail } }));
    }
  };

  const [remediations, setRemediations] = useState<Record<number, RemediationState>>({});
  const remediate = async (id: number, action: string) => {
    setRemediations((p) => ({ ...p, [id]: { loading: action } }));
    try {
      const { data } = await remediateIncident(id, action);
      if (data.command_id) {
        // Action exécutée par l'agent : on suit la commande jusqu'au résultat.
        setRemediations((p) => ({ ...p, [id]: { text: "⏳ En attente de l'agent…", ok: true } }));
        pollCommand(id, data.command_id);
      } else {
        setRemediations((p) => ({
          ...p,
          [id]: { text: data.detail, ok: data.status === "success" },
        }));
        refresh();
      }
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Action impossible.";
      setRemediations((p) => ({ ...p, [id]: { text: detail, ok: false } }));
    }
  };

  const pollCommand = (incidentId: number, commandId: number) => {
    let tries = 0;
    const timer = setInterval(async () => {
      tries++;
      try {
        const { data } = await getAgentCommand(commandId);
        if (data.status === "done" || data.status === "failed") {
          clearInterval(timer);
          setRemediations((p) => ({
            ...p,
            [incidentId]: { text: data.result ?? "(aucun résultat)", ok: data.status === "done" },
          }));
        }
      } catch {
        /* on continue d'essayer */
      }
      if (tries >= 20) {
        clearInterval(timer);
        setRemediations((p) => ({
          ...p,
          [incidentId]: { text: "L'agent n'a pas répondu (hors ligne ?).", ok: false },
        }));
      }
    }, 3000);
  };

  if (loading && !incidents) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader title="Incident Center" subtitle="Gestion centralisée des alertes actives" />

      <MaintenancePanel />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Total actifs" value={list.length} icon={BellRing} accent={list.length ? "critical" : "ok"} />
        <MetricCard label="Critical" value={counts.CRITICAL} icon={BellRing} accent="critical" />
        <MetricCard label="Warning" value={counts.WARNING} icon={BellRing} accent="warning" />
        <MetricCard label="Acquittés" value={ackedCount} icon={BellRing} accent="info" />
      </div>

      <Card className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher (hôte, check, message)…" className="input w-full pl-9" />
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-border bg-bg-soft p-1">
          <Filter className="mx-1 h-4 w-4 text-ink-faint" />
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition",
                filter === f ? "bg-brand text-white" : "text-ink-soft hover:text-ink",
              )}
            >
              {f === "ALL" ? "Tous" : f}
            </button>
          ))}
        </div>
      </Card>

      {filtered.length === 0 ? (
        <p className="py-10 text-center text-sm text-status-ok">Aucun incident ne correspond 🎉</p>
      ) : (
        <MotionGrid className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {filtered.map((inc) => (
            <AlertCard
              key={inc.alert_id}
              incident={inc}
              acknowledged={inc.acknowledged}
              onAck={editable ? () => toggleAck(inc.alert_id, inc.acknowledged) : undefined}
              onAnalyze={analyze}
              analysis={analyses[inc.alert_id]}
              onRemediate={editable ? remediate : undefined}
              remediation={remediations[inc.alert_id]}
              onTicket={editable ? openTicket : undefined}
              ticketBusy={ticketBusy === inc.alert_id}
            />
          ))}
        </MotionGrid>
      )}
    </div>
  );
}
