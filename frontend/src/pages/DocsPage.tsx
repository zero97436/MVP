import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { BookOpen, Search } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { DOC_SECTIONS } from "../lib/docs";

export default function DocsPage() {
  const { hash } = useLocation();
  const [q, setQ] = useState("");

  // Défilement vers l'ancre demandée (ex. /docs#hosts) au chargement / changement de hash.
  useEffect(() => {
    if (!hash) return;
    const id = decodeURIComponent(hash.slice(1));
    const el = document.getElementById(id);
    if (el) {
      // Léger délai : laisse le rendu se poser avant de défiler.
      const t = setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
      return () => clearTimeout(t);
    }
  }, [hash]);

  const sections = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return DOC_SECTIONS;
    return DOC_SECTIONS.filter((s) =>
      (s.title + " " + s.summary + " " + s.body.join(" ") + " " + (s.tips ?? []).join(" "))
        .toLowerCase()
        .includes(needle),
    );
  }, [q]);

  return (
    <div className="space-y-6">
      <PageHeader title="Documentation" subtitle="Guide d'utilisation, section par section" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
        {/* Sommaire */}
        <aside className="lg:sticky lg:top-4 lg:self-start">
          <Card className="p-3">
            <p className="mb-2 px-2 text-[11px] uppercase tracking-wide text-ink-faint">Sommaire</p>
            <nav className="space-y-0.5">
              {DOC_SECTIONS.map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className="block truncate rounded-md px-2 py-1.5 text-sm text-ink-soft transition hover:bg-bg-soft hover:text-ink"
                >
                  {s.title}
                </a>
              ))}
            </nav>
          </Card>
        </aside>

        {/* Contenu */}
        <div className="space-y-5">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Rechercher dans la documentation…"
              className="input w-full pl-9"
            />
          </div>

          {sections.length === 0 && (
            <p className="text-sm text-ink-faint">Aucune section ne correspond à « {q} ».</p>
          )}

          {sections.map((s) => (
            <Card key={s.id} id={s.id} className="scroll-mt-4">
              <div className="mb-2 flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-brand" />
                <h2 className="text-lg font-semibold text-ink">{s.title}</h2>
              </div>
              <p className="mb-3 text-sm font-medium text-ink-soft">{s.summary}</p>
              <div className="space-y-2">
                {s.body.map((p, i) => (
                  <p key={i} className="text-sm leading-relaxed text-ink-soft">{p}</p>
                ))}
              </div>
              {s.tips && s.tips.length > 0 && (
                <div className="mt-3 rounded-lg border border-border bg-bg-soft/50 p-3">
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">À savoir</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-ink-soft">
                    {s.tips.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
