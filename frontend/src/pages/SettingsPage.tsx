import { useEffect, useState } from "react";
import { Mail, Webhook, Plus, Users, Trash2, ShieldAlert, Database, Eraser, MessageSquare, Send, Users2, Hash, Phone, Terminal } from "lucide-react";
import {
  createChannel,
  createUser,
  deleteUser,
  getDbStats,
  listChannels,
  listUsers,
  runRetention,
  testChannel,
  updateUser,
  type DbStats,
} from "../api/endpoints";
import type { NotificationChannel, User, UserRole } from "../types";

type ChannelType = NotificationChannel["type"];
const CHANNEL_TYPES: ChannelType[] = ["webhook", "email", "slack", "telegram", "teams", "discord", "sms", "script"];
const CHANNEL_PLACEHOLDER: Record<ChannelType, string> = {
  webhook: '{"url": "https://..."}',
  email: '{"to": "ops@exemple.com"}',
  slack: '{"webhook_url": "https://hooks.slack.com/services/..."}',
  telegram: '{"bot_token": "123:ABC", "chat_id": "123456789"}',
  teams: '{"webhook_url": "https://outlook.office.com/webhook/..."}',
  discord: '{"webhook_url": "https://discord.com/api/webhooks/..."}',
  sms: '{"account_sid": "AC...", "auth_token": "...", "from": "+33...", "to": "+33..."}',
  script: '{"command": "/opt/scripts/handler.sh"}',
};
const CHANNEL_ICON: Record<ChannelType, typeof Mail> = {
  email: Mail,
  webhook: Webhook,
  slack: MessageSquare,
  telegram: Send,
  teams: Users2,
  discord: Hash,
  sms: Phone,
  script: Terminal,
};
import { formatDate } from "../lib/format";
import { PageHeader } from "../components/ui/PageHeader";
import { BrandingPanel } from "../components/BrandingPanel";
import { Card, SectionTitle } from "../components/ui/Card";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { SystemHealthCard } from "../components/SystemHealthCard";
import { useAuth } from "../lib/auth";
import { isAdmin, ROLE_LABEL } from "../lib/permissions";

const EMPTY_CHANNEL = { name: "", type: "webhook" as ChannelType, config_json: '{"url": ""}', escalation_only: false, active_hours: "" };
const EMPTY_USER = { email: "", password: "", role: "viewer" as UserRole };
const ROLES: UserRole[] = ["admin", "operator", "viewer"];

export default function SettingsPage() {
  const { user } = useAuth();
  const admin = isAdmin(user);

  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chForm, setChForm] = useState(EMPTY_CHANNEL);

  const [users, setUsers] = useState<User[]>([]);
  const [userForm, setUserForm] = useState(EMPTY_USER);
  const [userErr, setUserErr] = useState<string | null>(null);

  const [stats, setStats] = useState<DbStats | null>(null);
  const [purging, setPurging] = useState(false);

  const load = () => {
    setLoading(true);
    listChannels()
      .then((r) => setChannels(r.data))
      .catch(() => setError("Erreur de chargement"))
      .finally(() => setLoading(false));
    if (admin) {
      listUsers().then((r) => setUsers(r.data)).catch(() => {});
      getDbStats().then((r) => setStats(r.data)).catch(() => {});
    }
  };
  useEffect(load, [admin]);

  const purge = async () => {
    setPurging(true);
    try {
      const { data } = await runRetention();
      alert(`Purge terminée : ${data.total} ligne(s) supprimée(s).`);
      getDbStats().then((r) => setStats(r.data)).catch(() => {});
    } finally {
      setPurging(false);
    }
  };

  const submitChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(chForm.config_json || "{}");
    } catch {
      alert("config_json invalide");
      return;
    }
    await createChannel({
      name: chForm.name, type: chForm.type, config_json: config,
      escalation_only: chForm.escalation_only, active_hours: chForm.active_hours || null,
    });
    setChForm(EMPTY_CHANNEL);
    load();
  };

  const submitUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserErr(null);
    try {
      await createUser(userForm);
      setUserForm(EMPTY_USER);
      load();
    } catch {
      setUserErr("Création impossible (email déjà utilisé ou mot de passe trop court).");
    }
  };

  const testCh = async (id: number) => {
    try {
      await testChannel(id);
      alert("Notification de test envoyée ✅");
    } catch {
      alert("Échec de l'envoi — vérifie la configuration du canal (voir logs backend).");
    }
  };

  const changeRole = async (u: User, role: UserRole) => {
    await updateUser(u.id, { role });
    load();
  };

  const removeUser = async (u: User) => {
    if (confirm(`Supprimer l'utilisateur ${u.email} ?`)) {
      await deleteUser(u.id);
      load();
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Canaux de notification, utilisateurs et préférences" />

      <BrandingPanel />

      {admin && <SystemHealthCard />}

      {/* Gestion des utilisateurs (admin) */}
      {admin && (
        <Card>
          <SectionTitle title="Utilisateurs & rôles" icon={Users} />
          <form onSubmit={submitUser} className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-4">
            <input required type="email" placeholder="Email" value={userForm.email}
              onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} className="input" />
            <input required type="password" placeholder="Mot de passe (min 6)" value={userForm.password}
              onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} className="input" />
            <select value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value as UserRole })} className="input">
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
            <button className="btn-primary"><Plus className="h-4 w-4" /> Ajouter</button>
          </form>
          {userErr && <p className="mb-3 text-sm text-status-critical">{userErr}</p>}

          <div className="space-y-2">
            {users.map((u) => (
              <div key={u.id} className="flex items-center gap-3 rounded-lg border border-border bg-bg-soft/50 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink">{u.email}</p>
                  <p className="text-xs text-ink-faint">{u.is_active ? "actif" : "inactif"}</p>
                </div>
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u, e.target.value as UserRole)}
                  disabled={u.id === user?.id}
                  className="input py-1.5 text-xs"
                  title={u.id === user?.id ? "Vous ne pouvez pas changer votre propre rôle ici" : undefined}
                >
                  {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                </select>
                {u.id !== user?.id && (
                  <button onClick={() => removeUser(u)} className="text-status-critical/80 hover:text-status-critical">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Maintenance / rétention (admin) */}
      {admin && stats && (
        <Card>
          <SectionTitle
            title="Base de données & rétention"
            icon={Database}
            action={
              <button onClick={purge} disabled={purging} className="btn-ghost px-3 py-1.5 text-xs">
                <Eraser className="h-3.5 w-3.5" /> {purging ? "Purge..." : "Purger maintenant"}
              </button>
            }
          />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <RetentionStat label="Résultats de checks" stat={stats.check_results} days={stats.retention_days.check_results} />
            <RetentionStat label="Métriques (brut)" stat={stats.host_metrics} days={stats.retention_days.host_metrics} />
            <RetentionStat label="Métriques (horaire)" stat={stats.host_metrics_hourly} days={stats.retention_days.host_metrics_hourly} />
            <RetentionStat label="Alertes" stat={stats.alerts} days={stats.retention_days.resolved_alerts} />
          </div>
          <p className="mt-3 text-xs text-ink-faint">
            La purge automatique tourne via le scheduler ; les données au-delà de la fenêtre
            de rétention sont supprimées (configurable via variables d'environnement).
          </p>
        </Card>
      )}

      {/* Canaux de notification */}
      <Card>
        <SectionTitle title="Canaux de notification" />
        {admin ? (
          <form onSubmit={submitChannel} className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input required placeholder="Nom" value={chForm.name} onChange={(e) => setChForm({ ...chForm, name: e.target.value })} className="input" />
            <select
              value={chForm.type}
              onChange={(e) => {
                const t = e.target.value as ChannelType;
                setChForm({ ...chForm, type: t, config_json: CHANNEL_PLACEHOLDER[t] });
              }}
              className="input"
            >
              {CHANNEL_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input placeholder={CHANNEL_PLACEHOLDER[chForm.type]} value={chForm.config_json} onChange={(e) => setChForm({ ...chForm, config_json: e.target.value })} className="input font-mono" />
            <label className="flex items-center gap-2 text-sm text-ink-soft">
              <input type="checkbox" checked={chForm.escalation_only} onChange={(e) => setChForm({ ...chForm, escalation_only: e.target.checked })} />
              Escalade uniquement (astreinte)
            </label>
            <input placeholder="Plage horaire ex. 08:00-20:00 (vide = 24/7)" value={chForm.active_hours} onChange={(e) => setChForm({ ...chForm, active_hours: e.target.value })} className="input sm:col-span-2" />
            <button className="btn-primary sm:col-span-3"><Plus className="h-4 w-4" /> Ajouter le canal</button>
          </form>
        ) : (
          <p className="mb-4 flex items-center gap-2 rounded-lg border border-border bg-bg-soft/50 p-3 text-sm text-ink-faint">
            <ShieldAlert className="h-4 w-4" /> Seul un administrateur peut configurer les canaux.
          </p>
        )}

        {loading ? <Loading /> : error ? <ErrorState message={error} /> :
          channels.length === 0 ? <EmptyState message="Aucun canal configuré." /> : (
          <div className="space-y-2">
            {channels.map((ch) => {
              const Icon = CHANNEL_ICON[ch.type] ?? Webhook;
              return (
                <div key={ch.id} className="flex items-center gap-3 rounded-lg border border-border bg-bg-soft/50 px-3 py-2.5">
                  <span className="rounded-lg bg-bg p-2 text-ink-soft">
                    <Icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2 text-sm font-medium text-ink">
                      {ch.name}
                      {ch.escalation_only && <span className="rounded bg-status-warning/15 px-1.5 py-0.5 text-[10px] text-status-warning">astreinte</span>}
                      {ch.active_hours && <span className="rounded bg-bg px-1.5 py-0.5 text-[10px] text-ink-faint">{ch.active_hours}</span>}
                    </p>
                    <p className="truncate font-mono text-xs text-ink-faint">{JSON.stringify(ch.config_json)}</p>
                  </div>
                  <span className="rounded-full bg-bg px-2 py-0.5 text-xs text-ink-soft">{ch.type}</span>
                  {admin && (
                    <button onClick={() => testCh(ch.id)} className="btn-ghost px-2.5 py-1.5 text-xs">
                      <Send className="h-3.5 w-3.5" /> Tester
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <p className="text-sm text-ink-faint">
        SMTP et autres secrets sont configurés via variables d'environnement (voir .env).
      </p>
    </div>
  );
}

function RetentionStat({
  label,
  stat,
  days,
}: {
  label: string;
  stat: { count: number; oldest: string | null };
  days: number;
}) {
  return (
    <div className="rounded-lg border border-border bg-bg-soft/50 p-3">
      <p className="text-xs uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-ink">{stat.count.toLocaleString()}</p>
      <p className="mt-1 text-xs text-ink-faint">
        rétention {days} j · plus ancien : {stat.oldest ? formatDate(stat.oldest) : "—"}
      </p>
    </div>
  );
}
