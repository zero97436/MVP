import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { HelpCircle } from "lucide-react";

export function PageHeader({
  title,
  subtitle,
  actions,
  helpTopic,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  /** Ancre de documentation : ajoute un lien « Aide » vers /docs#<helpTopic>. */
  helpTopic?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-wrap items-end justify-between gap-3"
    >
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-ink-soft">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        {actions}
        {helpTopic && (
          <Link
            to={`/docs#${helpTopic}`}
            title="Aide sur cette section"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium text-ink-soft transition hover:border-ink-faint/60 hover:text-ink"
          >
            <HelpCircle className="h-4 w-4" />
            <span className="hidden sm:inline">Aide</span>
          </Link>
        )}
      </div>
    </motion.div>
  );
}
