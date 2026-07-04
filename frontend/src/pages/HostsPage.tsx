import { useEffect, useMemo, useState } from "react";
import { Plus, Search, Radar, Upload } from "lucide-react";
import { DiscoveryPanel } from "../components/DiscoveryPanel";
import { createHost, deleteHost, listChecks, listHosts, updateHost } from "../api/endpoints";
import type { Check, Host } from "../types";
import type { HostView } from "../components/ui/HostCard";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, MotionGrid } from "../components/ui/Card";
import { HostCard } from "../components/ui/HostCard";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { buildHostViews } from "../lib/fleet";
import { getLicense, type LicenseInfo } from "../api/endpoints";
import { ImportPanel } from "../components/ImportPanel";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

const EMPTY = { name: "", hostname_or_ip: "", description: "", environment: "production", parent_host_id: 0, location: "", latitude: "", longitude: "" };

export default function HostsPage() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [showDiscovery, setShowDiscovery] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [limitError, setLimitError] = useState<string | null>(null);
  const { user } = useAuth();
  const editable = canEdit(user);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY);
    setShowForm((s) => editingId !== null ? true : !s);
  };

  const openEdit = (h: HostView) => {
    setEditingId(h.id);
    setForm({
      name: h.name,
      hostname_or_ip: h.hostname_or_ip,
      description: h.description ?? "",
      environment: h.environment,
      parent_host_id: h.parent_host_id ?? 0,
      location: h.location ?? "",
      latitude: h.latitude != null ? String(h.latitude) : "",
      longitude: h.longitude != null ? String(h.longitude) : "",
    });
    setShowForm(true);
  };

  const load = () => {
    setLoading(true);
    Promise.all([listHosts(), listChecks()])
      .then(([h, c]) => {
        setHosts(h.data);
        setChecks(c.data);
        getLicense().then((r) => setLicense(r.data)).catch(() => {});
      })
      .catch(() => setError("Erreur de chargement"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); getLicense().then((r) => setLicense(r.data)).catch(() => {}); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      ...form,
      parent_host_id: form.parent_host_id || null,
      location: form.location || null,
      latitude: form.latitude === "" ? null : Number(form.latitude),
      longitude: form.longitude === "" ? null : Number(form.longitude),
    };
    try {
      if (editingId !== null) {
        await updateHost(editingId, payload);
      } else {
        await createHost(payload);
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (detail) { setLimitError(detail); return; }
      throw err;
    }
    setLimitError(null);
    setForm(EMPTY);
    setEditingId(null);
    setShowForm(false);
    load();
  };

  const remove = async (id: number) => {
    if (confirm("Supprimer cet hôte ?")) {
      await deleteHost(id);
      load();
    }
  };

  const views = useMemo(() => buildHostViews(hosts, checks), [hosts, checks]);
  const filtered = views.filter(
    (h) =>
      h.name.toLowerCase().includes(q.toLowerCase()) ||
      h.hostname_or_ip.toLowerCase().includes(q.toLowerCase()) ||
      h.environment.toLowerCase().includes(q.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hosts"
        subtitle={license ? `${license.used}/${license.max_hosts} hôtes (plan ${license.plan === "free" ? "gratuit" : license.plan})` : `${views.length} hôtes supervisés`}
        actions={
          editable && (
            <div className="flex items-center gap-2">
              <button onClick={() => setShowDiscovery((s) => !s)} className="btn-ghost">
                <Radar className="h-4 w-4" /> Découverte
              </button>
              <button onClick={() => setShowImport((s) => !s)} className="btn-ghost">
                <Upload className="h-4 w-4" /> Importer
              </button>
              <button onClick={openCreate} className="btn-primary">
                <Plus className="h-4 w-4" />
                {showForm && editingId === null ? "Annuler" : "Nouvel hôte"}
              </button>
            </div>
          )
        }
      />

      {limitError && (
        <div className="card border-l-4 border-status-warning bg-status-warning/5 p-4 text-sm text-ink">
          ⚠️ {limitError}
          <button onClick={() => setLimitError(null)} className="ml-3 text-xs text-ink-faint hover:text-ink">fermer</button>
        </div>
      )}

      {showImport && editable && <ImportPanel onImported={load} />}

      {showDiscovery && editable && <DiscoveryPanel onImported={load} />}

      {showForm && (
        <Card>
          <p className="mb-3 text-sm font-medium text-ink-soft">
            {editingId !== null ? "Modifier l'hôte" : "Nouvel hôte"}
          </p>
          <form onSubmit={submit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <input required placeholder="Nom" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            <input required placeholder="Hostname ou IP" value={form.hostname_or_ip} onChange={(e) => setForm({ ...form, hostname_or_ip: e.target.value })} className="input" />
            <input placeholder="Environnement" value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })} className="input" />
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" />
            <input placeholder="Site (ex. Agence Paris)" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="input" />
            <div className="flex gap-2">
              <input placeholder="Latitude (ex. 48.8566)" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} className="input flex-1" />
              <input placeholder="Longitude (ex. 2.3522)" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} className="input flex-1" />
            </div>
            <label className="flex flex-col gap-1 text-xs text-ink-faint sm:col-span-2">
              Hôte parent (dépendance — si en panne, alertes des enfants supprimées)
              <select value={form.parent_host_id} onChange={(e) => setForm({ ...form, parent_host_id: Number(e.target.value) })} className="input">
                <option value={0}>Aucun</option>
                {hosts.filter((hh) => hh.id !== editingId).map((hh) => <option key={hh.id} value={hh.id}>{hh.name}</option>)}
              </select>
            </label>
            <div className="flex gap-2 sm:col-span-2">
              <button className="btn-primary flex-1">{editingId !== null ? "Enregistrer" : "Créer l'hôte"}</button>
              <button type="button" onClick={() => { setShowForm(false); setEditingId(null); setForm(EMPTY); }} className="btn-ghost">Annuler</button>
            </div>
          </form>
        </Card>
      )}

      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un hôte…" className="input w-full pl-9" />
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} />
      ) : filtered.length === 0 ? (
        <EmptyState message="Aucun hôte." />
      ) : (
        <MotionGrid className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((h) => (
            <HostCard key={h.id} host={h} onDelete={editable ? remove : undefined} onEdit={editable ? openEdit : undefined} />
          ))}
        </MotionGrid>
      )}
    </div>
  );
}
