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
import { CHECK_META, metaFor } from "../lib/checkMeta";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";
import { useI18n } from "../lib/i18n";

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
  const { t: tr, lang } = useI18n();
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
    setForm({ ...EMPTY, config_json: metaFor(EMPTY.type, lang).config });
    setShowForm((s) => editingId !== null ? true : !s);
  };

  // Changer le type : pré-remplit l'exemple de config (sauf si l'utilisateur l'a déjà modifié).
  const changeType = (type: CheckType) => {
    setForm((f) => {
      const wasExample = Object.values(CHECK_META).some((m) => m.config === f.config_json) || f.config_json === "{}" || f.config_json === "";
      return { ...f, type, config_json: wasExample ? metaFor(type, lang).config : f.config_json };
    });
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
      .catch(() => setError(tr("common.loadError")))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(form.config_json || "{}");
    } catch {
      alert(tr("chk.badJson"));
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
    if (confirm(tr("chk.confirmDelete"))) {
      await deleteCheck(id);
      load();
    }
  };

  const hostName = new Map(hosts.map((h) => [h.id, h.name]));

  return (
    <div className="space-y-6">
      <PageHeader
        helpTopic="checks"
        title="Checks"
        subtitle={`${checks.length} ${tr("chk.subtitle")}`}
        actions={
          editable && (
            <button onClick={openCreate} className="btn-primary">
              <Plus className="h-4 w-4" /> {showForm && editingId === null ? tr("common.cancel") : tr("chk.new")}
            </button>
          )
        }
      />

      {showForm && (
        <Card>
          <p className="mb-3 text-sm font-medium text-ink-soft">
            {editingId !== null ? tr("chk.edit") : tr("chk.new")}
          </p>
          <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
              {tr("chk.hostToMonitor")}
              <select value={form.host_id} onChange={(e) => setForm({ ...form, host_id: Number(e.target.value) })} className="input" required>
                <option value="">{tr("chk.chooseHost")}</option>
                {hosts.map((h) => <option key={h.id} value={h.id}>{h.name} ({h.hostname_or_ip})</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
              {tr("chk.controlType")}
              <select value={form.type} onChange={(e) => changeType(e.target.value as CheckType)} className="input">
                {CHECK_TYPES.map((t) => <option key={t} value={t}>{metaFor(t, lang).label}</option>)}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft sm:col-span-2">
              {tr("chk.nameLabel")}
              <input required placeholder={`${tr("chk.namePhPre")} ${metaFor(form.type, lang).label} ${tr("chk.namePhPost")}`} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            </label>

            {/* Aide contextuelle selon le type choisi */}
            <div className="rounded-lg border border-brand/25 bg-brand/5 p-3 text-xs text-ink-soft sm:col-span-2">
              <p className="font-medium text-ink">ℹ️ {metaFor(form.type, lang).desc}</p>
              {metaFor(form.type, lang).thresholds && (
                <p className="mt-1">{tr("chk.thresholdsWarnCrit")} {metaFor(form.type, lang).thresholds}.</p>
              )}
              {metaFor(form.type, lang).config !== "{}" && (
                <p className="mt-1">{tr("chk.configExpected")} <code className="rounded bg-bg-soft px-1">{metaFor(form.type, lang).config}</code></p>
              )}
            </div>

            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft sm:col-span-2">
              {tr("chk.configLabel")} {metaFor(form.type, lang).config === "{}" ? tr("chk.noConfig") : tr("chk.replaceEmpty")}
              <textarea value={form.config_json} onChange={(e) => setForm({ ...form, config_json: e.target.value })} className="input font-mono text-xs" rows={metaFor(form.type, lang).config.length > 60 ? 3 : 2} />
            </label>

            <div className="grid grid-cols-3 gap-2 sm:col-span-2">
              <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
                {tr("chk.interval")}
                <input type="number" value={form.interval_seconds} onChange={(e) => setForm({ ...form, interval_seconds: Number(e.target.value) })} className="input" />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
                {tr("chk.warnThreshold")} {metaFor(form.type, lang).thresholds ? "" : tr("chk.optional")}
                <input type="number" placeholder="—" value={form.warning_threshold} onChange={(e) => setForm({ ...form, warning_threshold: e.target.value })} className="input" />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
                {tr("chk.critThreshold")} {metaFor(form.type, lang).thresholds ? "" : tr("chk.optional")}
                <input type="number" placeholder="—" value={form.critical_threshold} onChange={(e) => setForm({ ...form, critical_threshold: e.target.value })} className="input" />
              </label>
            </div>

            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
              {tr("chk.maxDelay")}
              <input type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} className="input" />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-ink-soft">
              {tr("chk.executedBy")}
              <select value={form.executor_host_id} onChange={(e) => setForm({ ...form, executor_host_id: Number(e.target.value) })} className="input">
                <option value={0}>{tr("chk.centralDefault")}</option>
                {hosts.map((h) => <option key={h.id} value={h.id}>{tr("chk.probeAgent")} {h.name}</option>)}
              </select>
            </label>

            <div className="flex gap-2 sm:col-span-2">
              <button className="btn-primary flex-1">{editingId !== null ? tr("common.save") : tr("chk.createBtn")}</button>
              <button type="button" onClick={() => { setShowForm(false); setEditingId(null); setForm(EMPTY); }} className="btn-ghost">{tr("common.cancel")}</button>
            </div>
          </form>
        </Card>
      )}

      {loading ? <Loading /> : error ? <ErrorState message={error} /> :
        checks.length === 0 ? <EmptyState message={tr("chk.empty")} /> : (
        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-bg-soft/50 text-left text-xs uppercase tracking-wide text-ink-faint">
              <tr>
                <th className="px-4 py-3">{tr("chk.colName")}</th>
                <th className="px-4 py-3">{tr("ten.host")}</th>
                <th className="px-4 py-3">{tr("chk.colType")}</th>
                <th className="px-4 py-3">{tr("chk.executedBy")}</th>
                <th className="px-4 py-3">{tr("chk.colInterval")}</th>
                <th className="px-4 py-3">{tr("cd.status")}</th>
                <th className="px-4 py-3 text-right">{tr("common.actions")}</th>
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
                  <td className="px-4 py-3 text-ink-soft">{c.executor_host_id ? `${tr("chk.agentPrefix")} ${hostName.get(c.executor_host_id) ?? "?"}` : tr("chk.central")}</td>
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
