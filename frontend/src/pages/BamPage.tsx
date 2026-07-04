import { useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import {
  listBam, createBamService, deleteBamService, addBamComponent, removeBamComponent,
  listChecks, type BamService,
} from "../api/endpoints";
import type { Check } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, MotionGrid } from "../components/ui/Card";
import { StatusBadge, StatusDot } from "../components/ui/StatusBadge";
import { EmptyState, Loading } from "../components/States";
import { statusMeta } from "../lib/status";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";
import { cn } from "../lib/cn";

export default function BamPage() {
  const { user } = useAuth();
  const editable = canEdit(user);
  const [services, setServices] = useState<BamService[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", rule: "worst", description: "", category: "Applications métier", icon: "" });

  const load = () => {
    Promise.all([listBam(), listChecks()])
      .then(([s, c]) => { setServices(s.data); setChecks(c.data); })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    await createBamService({
      name: form.name, rule: form.rule, description: form.description || undefined,
      category: form.category, icon: form.icon || undefined,
    });
    setForm({ name: "", rule: "worst", description: "", category: form.category, icon: "" });
    setShowForm(false);
    load();
  };
  const addComp = async (bsId: number, checkId: number) => { await addBamComponent(bsId, { check_id: checkId }); load(); };
  const delComp = async (id: number) => { await removeBamComponent(id); load(); };
  const delSvc = async (id: number) => { if (confirm("Supprimer ce service métier ?")) { await deleteBamService(id); load(); } };

  if (loading) return <Loading />;
  const checkName = new Map(checks.map((c) => [c.id, c.name]));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Services métier"
        subtitle="Surveillance métier (BAM) — agrège des checks/hôtes avec une règle d'impact"
        actions={editable && (
          <button onClick={() => setShowForm((s) => !s)} className="btn-primary">
            <Plus className="h-4 w-4" /> {showForm ? "Annuler" : "Nouveau service"}
          </button>
        )}
      />

      {showForm && editable && (
        <Card>
          <form onSubmit={create} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input required placeholder="Nom (ex. Site e-commerce)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            <select value={form.rule} onChange={(e) => setForm({ ...form, rule: e.target.value })} className="input">
              <option value="worst">Règle : pire état (une panne = impacté)</option>
              <option value="percent">Règle : % de composants OK</option>
            </select>
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" />
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input" title="Couche (Vue Opérations)">
              <option>Applications métier</option>
              <option>Back-Office</option>
              <option>Infrastructure</option>
              <option>Général</option>
            </select>
            <select value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} className="input" title="Icône de la tuile">
              <option value="">Icône (auto)</option>
              <option value="cart">🛒 Boutique</option>
              <option value="truck">🚚 Logistique</option>
              <option value="warehouse">🏬 Entrepôt</option>
              <option value="mail">✉️ E-mail</option>
              <option value="finance">💵 Finance</option>
              <option value="hr">👥 RH</option>
              <option value="globe">🌐 Intranet/Web</option>
              <option value="server">🖥️ Serveur</option>
              <option value="database">🗄️ Base de données</option>
              <option value="cloud">☁️ Cloud</option>
              <option value="network">🔗 Réseau</option>
              <option value="shield">🛡️ Sécurité</option>
            </select>
            <button className="btn-primary sm:col-span-3">Créer</button>
          </form>
        </Card>
      )}

      {services.length === 0 ? (
        <EmptyState message="Aucun service métier. Crée-en un pour regrouper des checks critiques." />
      ) : (
        <MotionGrid className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {services.map((s) => {
            const meta = statusMeta(s.status);
            return (
              <Card key={s.id} className="border-l-4" >
                <div className="mb-3 flex items-start justify-between" style={{ borderColor: meta.color }}>
                  <div className="flex items-center gap-3">
                    <StatusDot status={s.status} pulse={s.status !== "OK"} />
                    <div>
                      <p className="font-semibold text-ink">{s.name}</p>
                      {s.description && <p className="text-xs text-ink-faint">{s.description}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={s.status} label={meta.label} />
                    {editable && <button onClick={() => delSvc(s.id)} className="text-status-critical/80 hover:text-status-critical"><Trash2 className="h-4 w-4" /></button>}
                  </div>
                </div>
                <p className="mb-2 text-xs text-ink-faint">
                  {s.ok_count}/{s.total} composant(s) OK · règle {s.rule === "worst" ? "pire état" : "% OK"}
                </p>
                <div className="space-y-1">
                  {s.components.map((c) => (
                    <div key={c.id} className="flex items-center gap-2 rounded-lg border border-border bg-bg-soft/50 px-2.5 py-1.5 text-sm">
                      <StatusDot status={c.status} />
                      <span className="flex-1 truncate text-ink-soft">{c.label}</span>
                      {editable && <button onClick={() => delComp(c.id)} className="text-ink-faint hover:text-status-critical"><X className="h-3.5 w-3.5" /></button>}
                    </div>
                  ))}
                  {s.components.length === 0 && <p className="text-xs text-ink-faint">Aucun composant.</p>}
                </div>
                {editable && (
                  <select
                    className={cn("input mt-3 text-xs")}
                    value=""
                    onChange={(e) => e.target.value && addComp(s.id, Number(e.target.value))}
                  >
                    <option value="">+ Ajouter un check…</option>
                    {checks.map((c) => <option key={c.id} value={c.id}>{checkName.get(c.id)}</option>)}
                  </select>
                )}
              </Card>
            );
          })}
        </MotionGrid>
      )}
    </div>
  );
}
