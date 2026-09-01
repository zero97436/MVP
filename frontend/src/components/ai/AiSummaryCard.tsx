import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";
import { getAiSummary } from "../../api/endpoints";
import { Card } from "../ui/Card";
import { useI18n } from "../../lib/i18n";

export function AiSummaryCard() {
  const { t } = useI18n();
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await getAiSummary();
      setText(data.summary);
      setModel(data.model);
    } catch (e: unknown) {
      setError(
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          t("ai.unavailable"),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-ink-soft">
          <Sparkles className="h-4 w-4 text-brand" /> {t("ai.healthSummary")}
          {model && <span className="ml-1 rounded-full bg-bg-soft px-2 py-0.5 text-[10px] normal-case text-ink-faint">{model}</span>}
        </h2>
        <button onClick={generate} disabled={loading} className="btn-ghost px-3 py-1.5 text-xs">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : text ? <RefreshCw className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
          {loading ? t("ai.generating") : text ? t("ai.regenerate") : t("ai.generate")}
        </button>
      </div>

      <AnimatePresence>
        {(text || error) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            {error ? (
              <p className="mt-3 text-sm text-status-critical">{error}</p>
            ) : (
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-soft">{text}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!text && !error && !loading && (
        <p className="mt-3 text-sm text-ink-faint">
          {t("ai.hint")}
        </p>
      )}
    </Card>
  );
}
