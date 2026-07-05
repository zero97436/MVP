import { useEffect, useState } from "react";
import { Building2, Plus, Trash2, Server, Users } from "lucide-react";
import {
  listTenants, createTenant, deleteTenant, assignHostTenant, assignUserTenant,
  listHosts, listUsers, type Tenant,
} from "../api/endpoints";
import type { Host, User } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { Loading } from "../components/States";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [businessOnly, setBusinessOnly] = useState(false);
  const [name, setName] = useState("");

  const load = () =>
    Promise.all([listTenants(), listHosts(), listUsers()])
      .then(([t, h, u]) => { setTenants(t.data); setHosts(h.data); setUsers(u.data); setBusinessOnly(false); })
      .catch((e) => { if (e?.response?.status === 403) setBusinessOnly(true); });

  useEffect(() => { load().finally(() => setLoading(false)); }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await createTenant(name.trim());
    setName("");
    load();
  };
  const remove = async (id: number) => {
    if (confirm("Supprimer ce tenant ? (ses hôtes et utilisateurs repassent en global)")) {
      await deleteTenant(id); load();
    }
  };
  const setHost = async (host_id: number, tenant_id: number) => {
    await assignHostTenant(host_id, tenant_id || null); load();
  };
  const setUser = async (user_id: number, tenant_id: number) => {
    await assignUserTenant(user_id, tenant_id || null); load();
  };

  if (loading) return <Loading />;

  if (businessOnly) {
    return (
      <div className="space-y-6">
        <PageHeader title="Tenants" subtitle="Multi-tenant MSP" />
        <Card>
          <div className="flex flex-col items-center gap-3 py-14 text-center">
            <Building2 className="h-12 w-12 text-ink-faint" />
            <p className="text-sm font-medium text-ink">Multi-tenant MSP — plan Business</p>
            <p className="max-w-md text-xs text-ink-faint">
              Gérez plusieurs clients cloisonnés sur une seule instance : chaque client
              ne voit que ses propres équipements, incidents et rapports. Vos équipes MSP
              gardent la vue globale. Disponible à partir du plan Business.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Tenants" subtitle="Multi-tenant MSP — clients cloisonnés sur une seule instance" />

      <Card>
        <SectionTitle title="Créer un tenant (client)" icon={Plus} />
        <form onSubmit={create} className="flex gap-2">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du client (ex. ACME Corp)" className="input flex-1" />
          <button className="btn-primary">Créer</button>
        </form>
      </Card>

      <MotionGrid className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {tenants.map((t) => (
          <div key={t.id} className="card p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand/15 text-brand"><Building2 className="h-4 w-4" /></span>
                <div>
                  <p className="font-semibold text-ink">{t.name}</p>
                  <p className="text-xs text-ink-faint">{t.slug}</p>
                </div>
              </div>
              <button onClick={() => remove(t.id)} className="text-status-critical/70 hover:text-status-critical"><Trash2 className="h-4 w-4" /></button>
            </div>
            <div className="mt-3 flex gap-4 text-xs text-ink-soft">
              <span className="flex items-center gap-1"><Server className="h-3.5 w-3.5" /> {t.hosts} hôte(s)</span>
              <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5" /> {t.users} utilisateur(s)</span>
            </div>
          </div>
        ))}
        {tenants.length === 0 && <p className="text-sm text-ink-faint">Aucun tenant. Créez-en un pour commencer.</p>}
      </MotionGrid>

      {/* Assignation des hôtes */}
      <Card className="overflow-hidden p-0">
        <div className="p-5 pb-2"><SectionTitle title="Assignation des hôtes" icon={Server} /></div>
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-bg-soft/50 text-left text-xs uppercase tracking-wide text-ink-faint">
            <tr><th className="px-4 py-2.5">Hôte</th><th className="px-4 py-2.5">IP</th><th className="px-4 py-2.5">Tenant</th></tr>
          </thead>
          <tbody>
            {hosts.map((h) => (
              <tr key={h.id} className="border-t border-border">
                <td className="px-4 py-2 text-ink">{h.name}</td>
                <td className="px-4 py-2 text-ink-faint">{h.hostname_or_ip}</td>
                <td className="px-4 py-2">
                  <select value={h.tenant_id ?? 0} onChange={(e) => setHost(h.id, Number(e.target.value))} className="input py-1 text-xs">
                    <option value={0}>— Global (non assigné) —</option>
                    {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Assignation des utilisateurs */}
      <Card className="overflow-hidden p-0">
        <div className="p-5 pb-2"><SectionTitle title="Rattachement des utilisateurs" icon={Users} /></div>
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-bg-soft/50 text-left text-xs uppercase tracking-wide text-ink-faint">
            <tr><th className="px-4 py-2.5">Utilisateur</th><th className="px-4 py-2.5">Rôle</th><th className="px-4 py-2.5">Tenant (vide = MSP global)</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-border">
                <td className="px-4 py-2 text-ink">{u.email}</td>
                <td className="px-4 py-2 text-ink-faint">{u.role}</td>
                <td className="px-4 py-2">
                  <select value={(u as User & { tenant_id?: number }).tenant_id ?? 0} onChange={(e) => setUser(u.id, Number(e.target.value))} className="input py-1 text-xs">
                    <option value={0}>— MSP global (voit tout) —</option>
                    {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
