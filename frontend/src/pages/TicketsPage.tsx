import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, ExternalLink, Ticket as TicketIcon, Zap, ListChecks, X, ChevronDown, ChevronUp, Pencil, Save, MessageSquare, Send, UserCheck } from "lucide-react";
import {
  listTickets, createTicket, setTicketStatus, deleteTicket, getTicketConfig,
  addTicketTask, updateTicketTask, deleteTicketTask,
  updateTicket, addTicketComment, deleteTicketComment, listTicketAssignees,
  type Ticket, type TicketConfig, type TicketAssignee,
} from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, MotionGrid } from "../components/ui/Card";
import { EmptyState, Loading } from "../components/States";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";
import { timeAgo } from "../lib/format";
import { cn } from "../lib/cn";

const STATUSES = ["open", "in_progress", "resolved", "closed"] as const;
const STATUS_LABEL: Record<string, string> = {
  open: "Ouvert", in_progress: "En cours", resolved: "Résolu", closed: "Clôturé",
};
const STATUS_COLOR: Record<string, string> = {
  open: "#EF4444", in_progress: "#F59E0B", resolved: "#10B981", closed: "#64748B",
};
const PRIO_COLOR: Record<string, string> = {
  low: "#64748B", medium: "#3B82F6", high: "#F59E0B", critical: "#EF4444",
};
const PRIO_LABEL: Record<string, string> = {
  low: "Basse", medium: "Moyenne", high: "Haute", critical: "Critique",
};

export default function TicketsPage() {
  const { user } = useAuth();
  const editable = canEdit(user);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [config, setConfig] = useState<TicketConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", priority: "medium", description: "" });

  const [assignees, setAssignees] = useState<TicketAssignee[]>([]);
  const load = () => {
    Promise.all([listTickets(), getTicketConfig(), listTicketAssignees()])
      .then(([t, c, a]) => { setTickets(t.data); setConfig(c.data); setAssignees(a.data); })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTicket({ title: form.title, priority: form.priority, description: form.description || undefined });
    setForm({ title: "", priority: "medium", description: "" });
    setShowForm(false);
    load();
  };
  const changeStatus = async (id: number, status: string) => { await setTicketStatus(id, status); load(); };
  const remove = async (id: number) => { if (confirm("Supprimer ce ticket ?")) { await deleteTicket(id); load(); } };

  const [newTask, setNewTask] = useState<Record<number, string>>({});
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const addTask = async (ticketId: number) => {
    const label = (newTask[ticketId] ?? "").trim();
    if (!label) return;
    await addTicketTask(ticketId, label);
    setNewTask((p) => ({ ...p, [ticketId]: "" }));
    load();
  };
  const toggleTask = async (taskId: number, done: boolean) => { await updateTicketTask(taskId, { done }); load(); };
  const removeTask = async (taskId: number) => { await deleteTicketTask(taskId); load(); };

  // Édition GLPI-like : un ticket à la fois, brouillon local.
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState({ title: "", description: "", priority: "medium" });
  const startEdit = (t: Ticket) => {
    setEditing(t.id);
    setDraft({ title: t.title, description: t.description ?? "", priority: t.priority });
  };
  const saveEdit = async () => {
    if (editing == null) return;
    await updateTicket(editing, { title: draft.title, description: draft.description, priority: draft.priority });
    setEditing(null);
    load();
  };

  // Suivis (commentaires).
  const [newComment, setNewComment] = useState<Record<number, string>>({});
  const [showComments, setShowComments] = useState<Record<number, boolean>>({});
  const postComment = async (ticketId: number) => {
    const body = (newComment[ticketId] ?? "").trim();
    if (!body) return;
    await addTicketComment(ticketId, body);
    setNewComment((p) => ({ ...p, [ticketId]: "" }));
    load();
  };
  const removeComment = async (id: number) => { await deleteTicketComment(id); load(); };
  const assign = async (ticketId: number, value: string) => {
    await updateTicket(ticketId, { assigned_to_id: value === "" ? null : Number(value) });
    load();
  };
  const [mineOnly, setMineOnly] = useState(false);

  if (loading) return <Loading />;
  const base = mineOnly ? tickets.filter((t) => t.assigned_to === user?.email) : tickets;
  const shown = filter === "all" ? base : base.filter((t) => t.status === filter);
  const counts = STATUSES.reduce((a, s) => ({ ...a, [s]: tickets.filter((t) => t.status === s).length }), {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tickets"
        subtitle="Gestion des incidents ITSM — création, suivi et intégration externe"
        actions={editable && (
          <button onClick={() => setShowForm((s) => !s)} className="btn-primary">
            <Plus className="h-4 w-4" /> {showForm ? "Annuler" : "Nouveau ticket"}
          </button>
        )}
      />

      {/* Bandeau intégration */}
      {config && (
        <div className="card flex items-center gap-3 p-4">
          <span className={cn("grid h-10 w-10 place-items-center rounded-lg", config.provider === "internal" ? "bg-bg-soft text-ink-soft" : "bg-brand/15 text-brand")}>
            <TicketIcon className="h-5 w-5" />
          </span>
          <div className="flex-1">
            <p className="text-sm font-medium text-ink">
              Fournisseur : <span className="uppercase">{config.provider}</span>
              {config.provider !== "internal" && <span className="text-ink-faint"> · {config.target}</span>}
            </p>
            <p className="text-xs text-ink-faint">
              {config.provider === "internal"
                ? "Tickets stockés localement. Configurez ITSM_PROVIDER (jira/servicenow/webhook) pour pousser vers un outil externe."
                : "Les nouveaux tickets sont poussés vers l'outil externe."}
            </p>
          </div>
          {config.auto_create && (
            <span className="flex items-center gap-1 rounded-full bg-status-critical/10 px-3 py-1.5 text-xs font-medium text-status-critical">
              <Zap className="h-3.5 w-3.5" /> Auto sur incident
            </span>
          )}
        </div>
      )}

      {showForm && editable && (
        <Card>
          <form onSubmit={create} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <input required placeholder="Titre du ticket" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input sm:col-span-3" />
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="input">
              {Object.entries(PRIO_LABEL).map(([k, v]) => <option key={k} value={k}>Priorité : {v}</option>)}
            </select>
            <textarea placeholder="Description (optionnel)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input sm:col-span-4" rows={2} />
            <button className="btn-primary sm:col-span-4">Créer le ticket</button>
          </form>
        </Card>
      )}

      {/* Filtres */}
      <div className="flex flex-wrap gap-2">
        <Chip active={filter === "all"} onClick={() => setFilter("all")} label={`Tous (${tickets.length})`} />
        {STATUSES.map((s) => (
          <Chip key={s} active={filter === s} onClick={() => setFilter(s)} label={`${STATUS_LABEL[s]} (${counts[s]})`} color={STATUS_COLOR[s]} />
        ))}
        <Chip
          active={mineOnly}
          onClick={() => setMineOnly((m) => !m)}
          label={`👤 À moi (${tickets.filter((t) => t.assigned_to === user?.email).length})`}
          color="#8B5CF6"
        />
      </div>

      {shown.length === 0 ? (
        <EmptyState message="Aucun ticket. Créez-en un ou ouvrez-en depuis un incident." />
      ) : (
        <MotionGrid className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {shown.map((t) => (
            <motion.div key={t.id} variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}>
              <div className="card border-l-4 p-4" style={{ borderColor: PRIO_COLOR[t.priority] }}>
                {editing === t.id ? (
                  /* --- Mode édition (GLPI-like) --- */
                  <div className="space-y-2">
                    <input
                      value={draft.title}
                      onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                      className="input w-full font-semibold"
                      placeholder="Titre"
                    />
                    <textarea
                      value={draft.description}
                      onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                      className="input w-full text-xs"
                      rows={6}
                      placeholder="Description"
                    />
                    <div className="flex items-center gap-2">
                      <select value={draft.priority} onChange={(e) => setDraft({ ...draft, priority: e.target.value })} className="input flex-1 text-xs">
                        {Object.entries(PRIO_LABEL).map(([k, v]) => <option key={k} value={k}>Priorité : {v}</option>)}
                      </select>
                      <button onClick={() => setEditing(null)} className="btn-ghost px-2.5 py-1.5 text-xs"><X className="h-3.5 w-3.5" /> Annuler</button>
                      <button onClick={saveEdit} className="btn-primary px-2.5 py-1.5 text-xs"><Save className="h-3.5 w-3.5" /> Enregistrer</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-ink">#{t.id} · {t.title}</p>
                      {t.description && (
                        <>
                          <p className={cn("mt-0.5 whitespace-pre-wrap text-xs text-ink-soft", !expanded[t.id] && "line-clamp-2")}>
                            {t.description}
                          </p>
                          <button
                            onClick={() => setExpanded((p) => ({ ...p, [t.id]: !p[t.id] }))}
                            className="mt-0.5 inline-flex items-center gap-0.5 text-[11px] text-brand hover:underline"
                          >
                            {expanded[t.id] ? <>Réduire <ChevronUp className="h-3 w-3" /></> : <>Lire tout <ChevronDown className="h-3 w-3" /></>}
                          </button>
                        </>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      {editable && (
                        <button onClick={() => startEdit(t)} className="btn-ghost px-2 py-1" title="Modifier le ticket">
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <span className="rounded-full px-2.5 py-1 text-[11px] font-semibold" style={{ background: `${PRIO_COLOR[t.priority]}1f`, color: PRIO_COLOR[t.priority] }}>
                        {PRIO_LABEL[t.priority]}
                      </span>
                    </div>
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-faint">
                  <span className="rounded-full px-2 py-0.5 font-medium" style={{ background: `${STATUS_COLOR[t.status]}1f`, color: STATUS_COLOR[t.status] }}>
                    {STATUS_LABEL[t.status]}
                  </span>
                  {t.assigned_to && (
                    <span className="flex items-center gap-1 rounded-full bg-brand/10 px-2 py-0.5 font-medium text-brand">
                      <UserCheck className="h-3 w-3" /> {t.assigned_to}
                    </span>
                  )}
                  {t.alert_id && <span>· incident #{t.alert_id}</span>}
                  {t.created_at && <span>· {timeAgo(t.created_at)}</span>}
                  {t.created_by && <span>· par {t.created_by}</span>}
                  {t.external_id && (
                    t.external_url
                      ? <a href={t.external_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand hover:underline">{t.external_id} <ExternalLink className="h-3 w-3" /></a>
                      : <span className="text-brand">{t.external_id}</span>
                  )}
                </div>
                {/* Tâches (checklist) */}
                <div className="mt-3 rounded-lg border border-border bg-bg-soft/40 p-2.5">
                  <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                    <ListChecks className="h-3.5 w-3.5" />
                    Tâches {t.tasks.length > 0 && `· ${t.tasks.filter((x) => x.done).length}/${t.tasks.length}`}
                  </p>
                  {t.tasks.length > 0 && (
                    <div className="mb-1.5 h-1 w-full overflow-hidden rounded-full bg-black/30">
                      <div
                        className="h-full rounded-full bg-status-ok transition-all"
                        style={{ width: `${(t.tasks.filter((x) => x.done).length / t.tasks.length) * 100}%` }}
                      />
                    </div>
                  )}
                  <div className="space-y-1">
                    {t.tasks.map((task) => (
                      <div key={task.id} className="group flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={task.done}
                          disabled={!editable}
                          onChange={(e) => toggleTask(task.id, e.target.checked)}
                          className="h-3.5 w-3.5 accent-emerald-500"
                        />
                        <span className={cn("flex-1 text-xs", task.done ? "text-ink-faint line-through" : "text-ink-soft")}>
                          {task.label}
                        </span>
                        {editable && (
                          <button onClick={() => removeTask(task.id)} className="opacity-0 transition-opacity group-hover:opacity-100">
                            <X className="h-3 w-3 text-ink-faint hover:text-status-critical" />
                          </button>
                        )}
                      </div>
                    ))}
                    {t.tasks.length === 0 && <p className="text-xs text-ink-faint">Aucune tâche.</p>}
                  </div>
                  {editable && (
                    <form
                      onSubmit={(e) => { e.preventDefault(); addTask(t.id); }}
                      className="mt-2 flex items-center gap-2"
                    >
                      <input
                        value={newTask[t.id] ?? ""}
                        onChange={(e) => setNewTask((p) => ({ ...p, [t.id]: e.target.value }))}
                        placeholder="Ajouter une tâche…"
                        className="input flex-1 py-1 text-xs"
                      />
                      <button type="submit" className="btn-ghost px-2 py-1"><Plus className="h-3.5 w-3.5" /></button>
                    </form>
                  )}
                </div>

                {/* Suivis (fil GLPI-like) */}
                <div className="mt-3 rounded-lg border border-border bg-bg-soft/40 p-2.5">
                  <button
                    onClick={() => setShowComments((p) => ({ ...p, [t.id]: !p[t.id] }))}
                    className="flex w-full items-center justify-between text-[11px] font-semibold uppercase tracking-wide text-ink-faint"
                  >
                    <span className="flex items-center gap-1.5">
                      <MessageSquare className="h-3.5 w-3.5" /> Suivis {t.comments.length > 0 && `· ${t.comments.length}`}
                    </span>
                    {showComments[t.id] ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  </button>
                  {showComments[t.id] && (
                    <>
                      <div className="mt-2 space-y-2">
                        {t.comments.map((c) => (
                          <div key={c.id} className="group rounded-lg border border-border bg-bg/60 px-2.5 py-1.5">
                            <div className="flex items-center justify-between text-[11px] text-ink-faint">
                              <span className="font-medium text-ink-soft">{c.author ?? "?"}</span>
                              <span className="flex items-center gap-2">
                                {c.created_at && timeAgo(c.created_at)}
                                {editable && (
                                  <button onClick={() => removeComment(c.id)} className="opacity-0 transition-opacity group-hover:opacity-100">
                                    <X className="h-3 w-3 hover:text-status-critical" />
                                  </button>
                                )}
                              </span>
                            </div>
                            <p className="mt-0.5 whitespace-pre-wrap text-xs text-ink-soft">{c.body}</p>
                          </div>
                        ))}
                        {t.comments.length === 0 && <p className="text-xs text-ink-faint">Aucun suivi.</p>}
                      </div>
                      {editable && (
                        <form onSubmit={(e) => { e.preventDefault(); postComment(t.id); }} className="mt-2 flex items-end gap-2">
                          <textarea
                            value={newComment[t.id] ?? ""}
                            onChange={(e) => setNewComment((p) => ({ ...p, [t.id]: e.target.value }))}
                            onKeyDown={(e) => {
                              // Entrée = envoyer ; Maj+Entrée = nouvelle ligne.
                              if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                postComment(t.id);
                              }
                            }}
                            rows={1}
                            placeholder="Ajouter un suivi… (Maj+Entrée = nouvelle ligne)"
                            className="input flex-1 resize-y py-1 text-xs"
                          />
                          <button type="submit" className="btn-ghost px-2 py-1.5"><Send className="h-3.5 w-3.5" /></button>
                        </form>
                      )}
                    </>
                  )}
                </div>

                {editable && (
                  <div className="mt-3 flex items-center gap-2">
                    <select value={t.status} onChange={(e) => changeStatus(t.id, e.target.value)} className="input flex-1 text-xs">
                      {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
                    </select>
                    <select
                      value={t.assigned_to_id ?? ""}
                      onChange={(e) => assign(t.id, e.target.value)}
                      className="input flex-1 text-xs"
                      title="Assigner ce ticket"
                    >
                      <option value="">Non assigné</option>
                      {assignees.map((a) => (
                        <option key={a.id} value={a.id}>{a.full_name || a.email}</option>
                      ))}
                    </select>
                    <button onClick={() => remove(t.id)} className="text-status-critical/80 hover:text-status-critical"><Trash2 className="h-4 w-4" /></button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </MotionGrid>
      )}
    </div>
  );
}

function Chip({ active, onClick, label, color }: { active: boolean; onClick: () => void; label: string; color?: string }) {
  return (
    <button
      onClick={onClick}
      className={cn("rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
        active ? "border-brand bg-brand/15 text-brand" : "border-border text-ink-soft hover:bg-bg-soft")}
      style={active && color ? { borderColor: color, background: `${color}1f`, color } : undefined}
    >
      {label}
    </button>
  );
}
