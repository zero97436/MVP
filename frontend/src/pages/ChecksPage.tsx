import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Play, Trash2, Pencil } from "lucide-react";
import { createCheck, deleteCheck, listChecks, listHosts, runCheck, updateCheck } from "../api/endpoints";
import type { Check, CheckType, Host } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { CHECK_TYPES } from "../lib/format";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

const EMPTY = {
  host_id: 0,
  name: "",
  type: "ping" as CheckType,
  interval_seconds: 60,
  timeout_seconds: 10,
  warning_threshold: "",
  critical_threshold: "",
  config_json: "{}",
  executor_host_id: 0, // 0 = serveur central
};

export default function ChecksPage() {
  const [checks, setChecks] = useState<Check[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { user } = useAuth();
  const editable = canEdit(user);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY);
    setShowForm((s) => editingId !== null ? true : !s);
  };

  const openEdit = (c: Check) => {
    setEditingId(c.id);
    setForm({
      host_id: c.host_id,
      name: c.name,
      type: c.type,
      interval_seconds: c.interval_seconds,
      timeout_seconds: c.timeout_seconds,
      warning_threshold: c.warning_threshold?.toString() ?? "",
      critical_threshold: c.critical_threshold?.toString() ?? "",
      config_json: JSON.stringify(c.config_json ?? {}),
      executor_host_id: c.executor_host_id ?? 0,
    });
    setShowForm(true);
  };

  const load = () => {
    setLoading(true);
    Promise.all([listChecks(), listHosts()])
      .then(([c, h]) => {
        setChecks(c.data);
        setHosts(h.data);
      })
      .catch(() => setError("Erreur de chargement"))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(form.config_json || "{}");
    } catch {
      alert("config_json invalide (JSON attendu)");
      return;
    }
    const payload = {
      host_id: Number(form.host_id) || hosts[0]?.id,
      name: form.name,
      type: form.type,
      interval_seconds: Number(form.interval_seconds),
      timeout_seconds: Number(form.timeout_seconds),
      warning_threshold: form.warning_threshold === "" ? null : Number(form.warning_threshold),
      critical_threshold: form.critical_threshold === "" ? null : Number(form.critical_threshold),
      config_json: config,
      executor_host_id: Number(form.executor_host_id) || null,
    };
    if (editingId !== null) {
      await updateCheck(editingId, payload);
    } else {
      await createCheck(payload);
    }
    setForm(EMPTY);
    setEditingId(null);
    setShowForm(false);
    load();
  };

  const run = async (id: number) => {
    await runCheck(id);
    load();
  };
  const remove = async (id: number) => {
    if (confirm("Supprimer ce check ?")) {
      await deleteCheck(id);
      load();
    }
  };

  const hostName = new Map(hosts.map((h) => [h.id, h.name]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Checks"
        subtitle={`${checks.length} sondes configurées`}
        actions={
          editable && (
            <button onClick={openCreate} className="btn-primary">
              <Plus className="h-4 w-4" /> {showForm && editingId === null ? "Annuler" : "Nouveau check"}
            </button>
          )
        }
      />

      {showForm && (
        <Card>
          <p className="mb-3 text-sm font-medium text-ink-soft">
            {editingId !== null ? "Modifier le check" : "Nouveau check"}
          </p>
          <form onSubmit={submit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <select value={form.host_id} onChange={(e) => setForm({ ...form, host_id: Number(e.target.value) })} className="input" required>
              <option value="">— Hôte —</option>
              {hosts.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as CheckType })} className="input">
              {CHECK_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input required placeholder="Nom" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            <div className="grid grid-cols-3 gap-2">
              <input type="number" placeholder="Intervalle (s)" value={form.interval_seconds} onChange={(e) => setForm({ ...form, interval_seconds: Number(e.target.value) })} className="input" title="Intervalle (s)" />
              <input type="number" placeholder="Warn" value={form.warning_threshold} onChange={(e) => setForm({ ...form, warning_threshold: e.target.value })} className="input" title="Seuil warning" />
              <input type="number" placeholder="Crit" value={form.critical_threshold} onChange={(e) => setForm({ ...form, critical_threshold: e.target.value })} className="input" title="Seuil critical" />
            </div>
            <input type="number" placeholder="Timeout (s)" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} className="input" title="Timeout (s)" />
            <label className="flex flex-col gap-1 text-xs text-ink-faint sm:col-span-2">
              Exécuté par (sonde)
              <select value={form.executor_host_id} onChange={(e) => setForm({ ...form, executor_host_id: Number(e.target.value) })} className="input" title="Qui exécute ce check">
                <option value={0}>Serveur central (par défaut)</option>
                {hosts.map((h) => <option key={h.id} value={h.id}>Agent : {h.name}</option>)}
              </select>
            </label>
            <textarea placeholder='config_json ex: {"port": 443} ou {"metric":"cpu_percent"}' value={form.config_json} onChange={(e) => setForm({ ...form, config_json: e.target.value })} className="input font-mono sm:col-span-2" rows={2} />
            <div className="flex gap-2 sm:col-span-2">
              <button className="btn-primary flex-1">{editingId !== null ? "Enregistrer" : "Créer le check"}</button>
              <button type="button" onClick={() => { setShowForm(false); setEditingId(null); setForm(EMPTY); }} className="btn-ghost">Annuler</button>
            </div>
          </form>
        </Card>
      )}

      {loading ? <Loading /> : error ? <ErrorState message={error} /> :
        checks.length === 0 ? <EmptyState message="Aucun check." /> : (
        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-bg-soft/50 text-left text-xs uppercase tracking-wide text-ink-faint">
              <tr>
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Hôte</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Exécuté par</th>
                <th className="px-4 py-3">Intervalle</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {checks.map((c) => (
                <tr key={c.id} className="border-t border-border transition hover:bg-bg-soft/40">
                  <td className="px-4 py-3">
                    <Link to={`/checks/${c.id}`} className="font-medium text-ink hover:text-brand">{c.name}</Link>
                  </td>
                  <td className="px-4 py-3 text-ink-soft">{hostName.get(c.host_id) ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-soft">{c.type}</td>
                  <td className="px-4 py-3 text-ink-soft">{c.executor_host_id ? `Agent : ${hostName.get(c.executor_host_id) ?? "?"}` : "Central"}</td>
                  <td className="px-4 py-3 text-ink-soft">{c.interval_seconds}s</td>
                  <td className="px-4 py-3"><StatusBadge status={c.last_status} size="xs" /></td>
                  <td className="px-4 py-3">
                    {editable ? (
                      <div className="flex items-center justify-end gap-3">
                        <button onClick={() => run(c.id)} className="inline-flex items-center gap-1 text-brand hover:underline"><Play className="h-3.5 w-3.5" /> Run</button>
                        <button onClick={() => openEdit(c)} className="inline-flex items-center gap-1 text-ink-soft hover:text-brand"><Pencil className="h-3.5 w-3.5" /></button>
                        <button onClick={() => remove(c.id)} className="inline-flex items-center gap-1 text-status-critical/80 hover:text-status-critical"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    ) : (
                      <span className="block text-right text-ink-faint">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
