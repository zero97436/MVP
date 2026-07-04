import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, Send, Bot, User as UserIcon, Wand2, Play, CheckCircle2, Trash2 } from "lucide-react";
import { chatAI, applyPlan, type AiPlan, type ApplyResult } from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { cn } from "../lib/cn";
import { useAuth } from "../lib/auth";
import { canEdit } from "../lib/permissions";

interface Msg {
  role: "user" | "assistant";
  content: string;
  plan?: AiPlan | null;
  applied?: ApplyResult | null;
}

const SUGGESTIONS = [
  "Quels hôtes sont en incident ?",
  "Le disque de mon PC est-il critique ?",
  "Résume l'état de la plateforme.",
  "Quels checks sont en WARNING ?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();
  const editable = canEdit(user);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || loading) return;
    const history = messages.slice(-6);
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const { data } = await chatAI(question, history);
      setMessages((m) => [...m, { role: "assistant", content: data.answer, plan: data.plan }]);
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Réponse impossible (IA injoignable ?).";
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${detail}` }]);
    } finally {
      setLoading(false);
    }
  };

  const applyFromPlan = async (index: number, plan: AiPlan) => {
    const hasDestructive = plan.operations.some((o) => o.destructive);
    if (hasDestructive && !confirm("Ce plan contient des suppressions définitives. Confirmer ?")) return;
    setApplying(true);
    try {
      const { data } = await applyPlan(plan);
      setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, plan: null, applied: data } : msg)));
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "⚠️ Application impossible (droits insuffisants ?)." }]);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col gap-4">
      <PageHeader title="Assistant IA" subtitle="Questions en langage naturel sur l'état de la plateforme" />

      <Card className="flex min-h-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand/15 text-brand">
                <Bot className="h-6 w-6" />
              </span>
              <p className="text-sm text-ink-faint">Pose une question sur tes hôtes, checks ou incidents.</p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => send(s)} className="btn-ghost px-3 py-1.5 text-xs">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}
            >
              <span className={cn("mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg",
                m.role === "user" ? "bg-bg-soft text-ink-soft" : "bg-brand/15 text-brand")}>
                {m.role === "user" ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </span>
              <div className={cn("max-w-[80%] space-y-2", m.role === "user" && "flex flex-col items-end")}>
                <div className={cn("whitespace-pre-wrap rounded-xl px-3.5 py-2.5 text-sm leading-relaxed",
                  m.role === "user" ? "bg-brand text-white" : "border border-border bg-bg-soft/60 text-ink-soft")}>
                  {m.content}
                </div>

                {/* Plan d'opérations proposé par l'IA */}
                {m.plan && (
                  <div className="rounded-xl border border-brand/30 bg-brand/5 p-3">
                    <p className="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
                      <Wand2 className="h-4 w-4 text-brand" /> Plan proposé ({m.plan.operations.length} opération·s)
                    </p>
                    <ul className="mb-3 space-y-1.5">
                      {m.plan.operations.map((o, oi) => (
                        <li key={oi} className={cn("flex items-start gap-2 text-xs", o.destructive ? "text-status-critical" : "text-ink-soft")}>
                          {o.destructive ? <Trash2 className="mt-0.5 h-3.5 w-3.5 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-faint" />}
                          {o.description}
                        </li>
                      ))}
                    </ul>
                    {editable ? (
                      <button onClick={() => applyFromPlan(i, m.plan!)} disabled={applying} className="btn-primary px-3 py-1.5 text-xs">
                        {applying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                        Appliquer le plan
                      </button>
                    ) : (
                      <p className="text-xs text-ink-faint">Rôle opérateur requis pour appliquer.</p>
                    )}
                  </div>
                )}

                {/* Résultat de l'application */}
                {m.applied && (
                  <div className="rounded-xl border border-status-ok/30 bg-status-ok/10 p-3 text-sm">
                    <p className="mb-1 flex items-center gap-2 font-medium text-status-ok">
                      <CheckCircle2 className="h-4 w-4" /> {m.applied.applied}/{m.applied.total} opération·s appliquée·s
                    </p>
                    <ul className="space-y-1">
                      {m.applied.results.map((r, ri) => (
                        <li key={ri} className="flex items-center gap-2 text-xs text-ink-soft">
                          <span className={cn("rounded px-1.5 py-0.5", r.status === "done" ? "bg-status-ok/15 text-status-ok" : "bg-status-critical/15 text-status-critical")}>{r.status}</span>
                          {r.host_id ? <Link to={`/hosts/${r.host_id}`} className="hover:underline">{r.detail}</Link> : r.detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-ink-faint">
              <Loader2 className="h-4 w-4 animate-spin" /> L'assistant réfléchit…
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="mt-3 flex items-center gap-2 border-t border-border pt-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ex : quel hôte est en critique ?"
            className="input flex-1"
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn-primary">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </form>
      </Card>
    </div>
  );
}
