import { useEffect, useState } from "react";
import { BookOpen, Plus, Trash2, RefreshCw, Sparkles, Upload, FileUp, PackagePlus } from "lucide-react";
import { listKnowledge, addKnowledge, deleteKnowledge, reindexKnowledge, importKnowledge, importStarterPack, type KnowledgeDoc } from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card, SectionTitle, MotionGrid } from "../components/ui/Card";
import { Loading } from "../components/States";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";
import { useI18n } from "../lib/i18n";

export default function KnowledgePage() {
  const { t } = useI18n();
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
  const remove = async (id: number) => { if (confirm(t("kn.confirmDelete"))) { await deleteKnowledge(id); load(); } };

  const [bulk, setBulk] = useState("");
  const importMarkdown = async () => {
    if (!bulk.trim()) return;
    setBusy(true);
    try { const { data } = await importKnowledge({ markdown: bulk }); setMsg(`${data.imported} ${t("kn.imported")}`); setBulk(""); load(); }
    finally { setBusy(false); }
  };
  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    try {
      const documents = await Promise.all(
        Array.from(files).map(async (f) => ({ title: f.name.replace(/\.[^.]+$/, ""), content: await f.text(), source: f.name })),
      );
      const { data } = await importKnowledge({ documents });
      setMsg(`${data.imported} ${t("kn.importedFrom")} ${files.length} ${t("kn.files")}`);
      load();
    } finally { setBusy(false); }
  };
  const loadStarter = async () => {
    setBusy(true);
    try { const { data } = await importStarterPack(); setMsg(`${data.imported} ${t("kn.starterAdded")}`); load(); }
    finally { setBusy(false); }
  };
  const reindex = async () => {
    setBusy(true);
    try { const { data } = await reindexKnowledge(); setMsg(`${data.embedded} ${t("kn.reindexed")}`); load(); }
    finally { setBusy(false); }
  };

  if (loading) return <Loading />;
  const embedded = docs.filter((d) => d.embedded).length;

  return (
    <div className="space-y-6">
      <PageHeader
        helpTopic="knowledge"
        titleKey="page.knowledge.title"
        subtitleKey="page.knowledge.sub"
        actions={editable && (
          <button onClick={reindex} disabled={busy} className="btn-ghost">
            <RefreshCw className="h-4 w-4" /> {t("kn.reindex")}
          </button>
        )}
      />

      <div className="card flex items-center gap-3 p-4">
        <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand/15 text-brand"><Sparkles className="h-5 w-5" /></span>
        <div className="flex-1 text-sm">
          <p className="text-ink">{docs.length} {t("kn.docsIndexed")} <b>{embedded}</b> {t("kn.semanticIndexed")}</p>
          <p className="text-xs text-ink-faint">
            {embedded < docs.length ? t("kn.keywordActive") : t("kn.semanticActive")}
          </p>
        </div>
      </div>
      {msg && <p className="text-xs text-status-ok">{msg}</p>}

      {/* Import en masse */}
      {editable && (
        <Card>
          <SectionTitle title={t("kn.bulkImport")} icon={Upload} />
          <div className="flex flex-wrap items-center gap-2">
            <label className="btn-ghost cursor-pointer">
              <FileUp className="h-4 w-4" /> {t("kn.importFiles")}
              <input type="file" accept=".md,.txt,.markdown" multiple className="hidden" onChange={(e) => onFiles(e.target.files)} />
            </label>
            <button onClick={loadStarter} disabled={busy} className="btn-ghost">
              <PackagePlus className="h-4 w-4" /> {t("kn.loadStarter")}
            </button>
          </div>
          <p className="mt-3 mb-1 text-xs text-ink-faint">{t("kn.pasteHint")}</p>
          <textarea value={bulk} onChange={(e) => setBulk(e.target.value)} rows={4}
                    placeholder={"## Problème A\nSolution A…\n\n## Problème B\nSolution B…"}
                    className="input w-full font-mono text-xs" />
          <button onClick={importMarkdown} disabled={busy || !bulk.trim()} className="btn-primary mt-2">{t("kn.importDoc")}</button>
        </Card>
      )}

      {editable && (
        <Card>
          <SectionTitle title={t("kn.addDoc")} icon={Plus} />
          <form onSubmit={add} className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <input required placeholder={t("kn.titlePh")} value={form.title}
                     onChange={(e) => setForm({ ...form, title: e.target.value })} className="input sm:col-span-2" />
              <input placeholder={t("kn.sourcePh")} value={form.source}
                     onChange={(e) => setForm({ ...form, source: e.target.value })} className="input" />
            </div>
            <textarea required placeholder={t("kn.contentPh")} value={form.content}
                      onChange={(e) => setForm({ ...form, content: e.target.value })} rows={5} className="input w-full" />
            <button disabled={busy} className="btn-primary">{t("common.add")}</button>
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
                    {d.chars} {t("kn.chars")} {d.source && `· ${d.source}`} · {d.embedded ? t("kn.semantic") : t("kn.keywords")}
                  </p>
                </div>
              </div>
              {editable && <button onClick={() => remove(d.id)} className="text-status-critical/70 hover:text-status-critical"><Trash2 className="h-4 w-4" /></button>}
            </div>
            <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs text-ink-soft">{d.content}</p>
          </div>
        ))}
        {docs.length === 0 && <p className="text-sm text-ink-faint">{t("kn.none")}</p>}
      </MotionGrid>
    </div>
  );
}
