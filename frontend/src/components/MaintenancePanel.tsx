import { useEffect, useState } from "react";
import { Wrench, Plus, Trash2 } from "lucide-react";
import {
  createMaintenance,
  deleteMaintenance,
  listHosts,
  listMaintenances,
} from "../api/endpoints";
import type { Host, Maintenance } from "../types";
import { Card, SectionTitle } from "./ui/Card";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";
import { formatDate } from "../lib/format";

const EMPTY = { host_id: 0, reason: "", starts_at: "", ends_at: "" };

export function MaintenancePanel() {
  const { user } = useAuth();
  const editable = canEdit(user);
  const [items, setItems] = useState<Maintenance[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [show, setShow] = useState(false);

  const load = () => {
    listMaintenances().then((r) => setItems(r.data)).catch(() => {});
    listHosts().then((r) => setHosts(r.data)).catch(() => {});
  };
  useEffect(load, []);

  const hostName = new Map(hosts.map((h) => [h.id, h.name]));
  const isActive = (m: Maintenance) => {
    const now = Date.now();
    return new Date(m.starts_at).getTime() <= now && new Date(m.ends_at).getTime() >= now;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.starts_at || !form.ends_at) return;
    await createMaintenance({
      host_id: form.host_id || null,
      reason: form.reason || undefined,
      starts_at: new Date(form.starts_at).toISOString(),
      ends_at: new Date(form.ends_at).toISOString(),
    });
    setForm(EMPTY);
    setShow(false);
    load();
  };

  const remove = async (id: number) => {
    if (confirm("Supprimer cette maintenance ?")) {
      await deleteMaintenance(id);
      load();
    }
  };

  return (
    <Card>
      <SectionTitle
        title="Maintenances planifiées"
        icon={Wrench}
        action={
          editable && (
            <button onClick={() => setShow((s) => !s)} className="btn-ghost px-2.5 py-1.5 text-xs">
              <Plus className="h-3.5 w-3.5" /> {show ? "Annuler" : "Planifier"}
            </button>
          )
        }
      />

      {show && editable && (
        <form onSubmit={submit} className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <select value={form.host_id} onChange={(e) => setForm({ ...form, host_id: Number(e.target.value) })} className="input">
            <option value={0}>Toute la plateforme (global)</option>
            {hosts.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
          </select>
          <input placeholder="Raison (ex. mise à jour)" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className="input" />
          <label className="flex flex-col gap-1 text-xs text-ink-faint">Début
            <input type="datetime-local" required value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })} className="input" />
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-faint">Fin
            <input type="datetime-local" required value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })} className="input" />
          </label>
          <button className="btn-primary sm:col-span-2">Planifier la maintenance</button>
        </form>
      )}

      {items.length === 0 ? (
        <p className="py-4 text-center text-sm text-ink-faint">Aucune maintenance planifiée.</p>
      ) : (
        <div className="space-y-2">
          {items.map((m) => (
            <div key={m.id} className="flex items-center gap-3 rounded-lg border border-border bg-bg-soft/50 px-3 py-2.5">
              {isActive(m) ? (
                <span className="rounded-full bg-status-warning/15 px-2 py-0.5 text-xs text-status-warning">active</span>
              ) : (
                <span className="rounded-full bg-bg px-2 py-0.5 text-xs text-ink-faint">planifiée</span>
              )}
              <div className="min-w-0 flex-1">
                <p className="text-sm text-ink">
                  {m.host_id ? `Hôte : ${hostName.get(m.host_id) ?? m.host_id}` : "Global"}
                  {m.reason ? ` — ${m.reason}` : ""}
                </p>
                <p className="text-xs text-ink-faint">{formatDate(m.starts_at)} → {formatDate(m.ends_at)}</p>
              </div>
              {editable && (
                <button onClick={() => remove(m.id)} className="text-status-critical/80 hover:text-status-critical">
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      <p className="mt-3 text-xs text-ink-faint">
        Pendant une maintenance, les checks tournent toujours mais aucune alerte n'est ouverte ni notifiée.
      </p>
    </Card>
  );
}
