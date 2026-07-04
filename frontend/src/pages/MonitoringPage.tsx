import { useEffect, useMemo, useState } from "react";
import { Activity, Server } from "lucide-react";
import { listChecks, listHosts, getSummary } from "../api/endpoints";
import type { Check, DashboardSummary, Host } from "../types";
import { usePolling } from "../hooks/usePolling";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { HealthCard } from "../components/ui/HostCard";
import { StatusDonut } from "../components/charts/StatusDonut";
import { LiveEventFeed } from "../components/live/LiveEventFeed";
import { Loading } from "../components/States";
import { buildHostViews } from "../lib/fleet";

export default function MonitoringPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const { data: summary } = usePolling<DashboardSummary>(() => getSummary().then((r) => r.data), 15000);
  const [ready, setReady] = useState(false);

  const reload = () => {
    Promise.all([listHosts(), listChecks()]).then(([h, c]) => {
      setHosts(h.data);
      setChecks(c.data);
      setReady(true);
    });
  };
  useEffect(() => {
    reload();
    const id = setInterval(reload, 15000);
    return () => clearInterval(id);
  }, []);

  const views = useMemo(() => buildHostViews(hosts, checks), [hosts, checks]);

  if (!ready) return <Loading />;

  return (
    <div className="space-y-6">
      <PageHeader title="Live Monitoring" subtitle="Flux d'événements et état de la flotte en temps réel" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card><LiveEventFeed height={420} /></Card>
        <Card className="lg:col-span-2">
          <SectionTitle title={`Health Overview — ${views.length} hôtes`} icon={Server} />
          <MotionGrid className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {views.map((h) => <HealthCard key={h.id} host={h} />)}
          </MotionGrid>
        </Card>
      </div>

      <Card className="lg:max-w-md">
        <SectionTitle title="Répartition des états" icon={Activity} />
        {summary && <StatusDonut counts={summary.status_counts} />}
      </Card>
    </div>
  );
}
