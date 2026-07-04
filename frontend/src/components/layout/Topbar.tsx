import { LogOut, Clock, ShieldCheck, Search, MonitorPlay } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../../lib/auth";
import { useNow } from "../../hooks/useNow";
import type { CheckStatus } from "../../types";
import { statusMeta } from "../../lib/status";
import { ROLE_LABEL } from "../../lib/permissions";
import { StatusDot } from "../ui/StatusBadge";

export function Topbar({ globalStatus }: { globalStatus: CheckStatus }) {
  const { user, logout } = useAuth();
  const now = useNow();
  const meta = statusMeta(globalStatus);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-bg-soft/60 px-6 backdrop-blur">
      <div className="flex items-center gap-3">
        <StatusDot status={globalStatus} pulse={globalStatus !== "OK"} />
        <span className="text-sm font-medium text-ink">
          Plateforme : <span className={meta.text}>{meta.label}</span>
        </span>
      </div>

      <div className="flex items-center gap-5 text-sm">
        <button
          onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }))}
          className="hidden items-center gap-2 rounded-lg border border-border bg-bg px-3 py-1.5 text-xs text-ink-faint transition-colors hover:text-ink md:flex"
          title="Recherche globale"
        >
          <Search className="h-3.5 w-3.5" /> Rechercher…
          <kbd className="rounded border border-border bg-bg-soft px-1.5 py-0.5 text-[10px]">Ctrl K</kbd>
        </button>
        <Link to="/tv" className="hidden items-center gap-1.5 rounded-lg border border-border bg-bg px-2.5 py-1.5 text-xs text-ink-faint transition-colors hover:text-ink lg:flex" title="Mode TV plein écran (écran mural)">
          <MonitorPlay className="h-3.5 w-3.5" /> TV
        </Link>
        <span className="hidden items-center gap-2 text-ink-soft sm:flex">
          <Clock className="h-4 w-4" />
          <span className="tabular-nums">{now.toLocaleString()}</span>
        </span>
        {user && (
          <span className="hidden items-center gap-1.5 md:flex">
            <span className="text-ink-faint">{user.email}</span>
            <span className="flex items-center gap-1 rounded-full bg-brand/10 px-2 py-0.5 text-xs text-brand">
              <ShieldCheck className="h-3 w-3" />
              {ROLE_LABEL[user.role]}
            </span>
          </span>
        )}
        <button onClick={logout} className="btn-ghost px-3 py-1.5" title="Déconnexion">
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Déconnexion</span>
        </button>
      </div>
    </header>
  );
}
