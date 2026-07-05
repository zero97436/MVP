import { useEffect, useState } from "react";
import { BookOpen, Plus, Trash2, RefreshCw, Sparkles } from "lucide-react";
import { listKnowledge, addKnowledge, deleteKnowledge, reindexKnowledge, type KnowledgeDoc } from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { Loading } from "../components/States";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

export default function KnowledgePage() {
  const { user } = useAuth();
  const editable = canEdit(user);
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", content: "", source: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () => listKnowledge().then((r) => setDocs(r.data)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) return;
    setBusy(true);
    try {
      await addKnowledge(form.title, form.content, form.source || undefined);
      setForm({ title: "", content: "", source: "" });
      load();
    } finally { setBusy(false); }
  };
  const remove = async (id: number) => { if (confirm("Supprimer ce document ?")) { await deleteKnowledge(id); load(); } };
  const reindex = async () => {
    setBusy(true);
    try { const { data } = await reindexKnowledge(); setMsg(`${data.embedded} document(s) ré-indexé(s) sémantiquement.`); load(); }
    finally { setBusy(false); }
  };

  if (loading) return <Loading />;
  const embedded = docs.filter((d) => d.embedded).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Connaissances"
        subtitle="Base de connaissances (RAG) — l'assistant IA s'appuie sur vos runbooks pour répondre"
        actions={editable && (
          <button onClick={reindex} disabled={busy} className="btn-ghost">
            <RefreshCw className="h-4 w-4" /> Ré-indexer
          </button>
        )}
      />

      <div className="card flex items-center gap-3 p-4">
        <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand/15 text-brand"><Sparkles className="h-5 w-5" /></span>
        <div className="flex-1 text-sm">
          <p className="text-ink">{docs.length} document(s) · <b>{embedded}</b> indexé(s) sémantiquement</p>
          <p className="text-xs text-ink-faint">
            {embedded < docs.length
              ? "Recherche par mots-clés active. Pour la recherche sémantique : ollama pull nomic-embed-text, puis « Ré-indexer »."
              : "Recherche sémantique active (embeddings Ollama)."}
          </p>
        </div>
      </div>
      {msg && <p className="text-xs text-status-ok">{msg}</p>}

      {editable && (
        <Card>
          <SectionTitle title="Ajouter un document (runbook, procédure, note)" icon={Plus} />
          <form onSubmit={add} className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <input required placeholder="Titre (ex. Redémarrer nginx)" value={form.title}
                     onChange={(e) => setForm({ ...form, title: e.target.value })} className="input sm:col-span-2" />
              <input placeholder="Source (optionnel)" value={form.source}
                     onChange={(e) => setForm({ ...form, source: e.target.value })} className="input" />
            </div>
            <textarea required placeholder="Contenu : procédure, commandes, contexte…" value={form.content}
                      onChange={(e) => setForm({ ...form, content: e.target.value })} rows={5} className="input w-full" />
            <button disabled={busy} className="btn-primary">Ajouter</button>
          </form>
        </Card>
      )}

      <MotionGrid className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {docs.map((d) => (
          <div key={d.id} className="card p-4">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand/10 text-brand"><BookOpen className="h-4 w-4" /></span>
                <div>
                  <p className="font-semibold text-ink">{d.title}</p>
                  <p className="text-xs text-ink-faint">
                    {d.chars} caractères {d.source && `· ${d.source}`} · {d.embedded ? "🔎 sémantique" : "mots-clés"}
                  </p>
                </div>
              </div>
              {editable && <button onClick={() => remove(d.id)} className="text-status-critical/70 hover:text-status-critical"><Trash2 className="h-4 w-4" /></button>}
            </div>
            <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs text-ink-soft">{d.content}</p>
          </div>
        ))}
        {docs.length === 0 && <p className="text-sm text-ink-faint">Aucun document. Ajoutez vos runbooks pour que l'IA s'en serve.</p>}
      </MotionGrid>
    </div>
  );
}
