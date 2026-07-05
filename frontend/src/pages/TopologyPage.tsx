import { useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  Position,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";
import { listChecks, listHosts } from "../api/endpoints";
import type { Check, Host } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { ErrorState, Loading } from "../components/States";
import { buildHostViews } from "../lib/fleet";
import { statusMeta } from "../lib/status";

export default function TopologyPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listHosts(), listChecks()])
      .then(([h, c]) => {
        setHosts(h.data);
        setChecks(c.data);
      })
      .catch(() => setError("Erreur de chargement"))
      .finally(() => setLoading(false));
  }, []);

  const { nodes, edges } = useMemo(() => {
    const views = buildHostViews(hosts, checks);
    const envs = [...new Set(views.map((v) => v.environment))].sort();
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Disposition arborescente gauche→droite, calculée séquentiellement pour
    // garantir l'absence de chevauchement, quel que soit le nombre d'hôtes.
    const COL_CORE = 0;
    const COL_ENV = 320;
    const COL_HOST = 660;
    const ROW = 78; // pas vertical
    const GROUP_GAP = 40; // espace entre deux groupes d'environnement

    let cursorY = 0;
    const envCenters: number[] = [];

    envs.forEach((env) => {
      const inEnv = views.filter((v) => v.environment === env);
      const startY = cursorY;

      inEnv.forEach((h) => {
        const meta = statusMeta(h.status);
        nodes.push({
          id: `host-${h.id}`,
          position: { x: COL_HOST, y: cursorY },
          data: { label: `${h.name}\n${h.hostname_or_ip}` },
          style: nodeStyle(meta.color),
          sourcePosition: Position.Left,
          targetPosition: Position.Left,
        });
        edges.push({
          id: `env-${env}-host-${h.id}`,
          source: `env-${env}`,
          target: `host-${h.id}`,
          animated: h.status !== "OK",
          markerEnd: { type: MarkerType.ArrowClosed, color: meta.color },
          style: { stroke: meta.color, strokeWidth: 2 },
        });
        cursorY += ROW;
      });

      if (inEnv.length === 0) cursorY += ROW;
      const envCenter = (startY + (cursorY - ROW)) / 2;
      envCenters.push(envCenter);

      // Pire statut de l'environnement → couleur du nœud env.
      const worst = inEnv.reduce<string>((acc, v) => {
        const order = { CRITICAL: 0, WARNING: 1, UNKNOWN: 2, OK: 3 } as Record<string, number>;
        return order[v.status] < order[acc] ? v.status : acc;
      }, "OK");
      nodes.push({
        id: `env-${env}`,
        position: { x: COL_ENV, y: envCenter },
        data: { label: `${env}  ·  ${inEnv.length}` },
        style: nodeStyle(statusMeta(worst as never).color),
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
      edges.push({
        id: `core-env-${env}`,
        source: "core",
        target: `env-${env}`,
        style: { stroke: "#334155", strokeWidth: 1.5 },
      });

      cursorY += GROUP_GAP;
    });

    // Plateforme centrée verticalement sur l'ensemble des environnements.
    const coreY = envCenters.length
      ? (Math.min(...envCenters) + Math.max(...envCenters)) / 2
      : 0;
    nodes.push({
      id: "core",
      position: { x: COL_CORE, y: coreY },
      data: { label: "🛰️ Opsora" },
      style: nodeStyle("#3B82F6", true),
      sourcePosition: Position.Right,
    });

    // Arêtes de dépendance (hôte parent -> enfant), en pointillés.
    const hostIds = new Set(views.map((v) => v.id));
    for (const v of views) {
      if (v.parent_host_id && hostIds.has(v.parent_host_id)) {
        edges.push({
          id: `dep-${v.parent_host_id}-${v.id}`,
          source: `host-${v.parent_host_id}`,
          target: `host-${v.id}`,
          animated: true,
          label: "dépend",
          style: { stroke: "#8B5CF6", strokeWidth: 1.5, strokeDasharray: "5 4" },
          labelStyle: { fill: "#8B5CF6", fontSize: 10 },
          labelBgStyle: { fill: "#111827" },
        });
      }
    }

    return { nodes, edges };
  }, [hosts, checks]);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader title="Network Topology" subtitle="Cartographie des hôtes par environnement — liens colorés selon l'état" />
      <Card className="p-0" >
        <div style={{ height: "70vh" }} className="rounded-xl">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            proOptions={{ hideAttribution: true }}
            nodesDraggable
          >
            <Background color="#1F2937" gap={20} />
            <Controls className="!border-border !bg-bg-soft" />
          </ReactFlow>
        </div>
      </Card>
    </div>
  );
}

function nodeStyle(color: string, strong = false): React.CSSProperties {
  return {
    background: "#111827",
    color: "#E5EAF2",
    border: `1px solid ${color}`,
    borderLeft: `4px solid ${color}`,
    borderRadius: 10,
    fontSize: 12,
    padding: "8px 12px",
    width: 200,
    textAlign: "center",
    whiteSpace: "pre-line",
    boxShadow: strong ? `0 0 24px -6px ${color}` : "none",
    fontWeight: strong ? 600 : 400,
  };
}
