import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  Search, Server, ListChecks, Ticket, History, ArrowRight, CornerDownLeft,
  LayoutDashboard, type LucideIcon,
} from "lucide-react";
import { globalSearch, type SearchResults } from "../api/endpoints";
import { cn } from "../lib/cn";

interface Item {
  key: string;
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  group: string;
  to: string;
  color?: string;
}

const PAGES: { label: string; to: string }[] = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Monitoring", to: "/monitoring" },
  { label: "Hosts", to: "/hosts" },
  { label: "Checks", to: "/checks" },
  { label: "Templates", to: "/templates" },
  { label: "Incidents", to: "/incidents" },
  { label: "Tickets", to: "/tickets" },
  { label: "APM", to: "/apm" },
  { label: "Conteneurs", to: "/containers" },
  { label: "Topology", to: "/topology" },
  { label: "Opérations", to: "/operations" },
  { label: "Métier (BAM)", to: "/bam" },
  { label: "Reports", to: "/reports" },
  { label: "Événements", to: "/events" },
  { label: "Assistant", to: "/assistant" },
  { label: "Settings", to: "/settings" },
];

const STATUS_COLOR: Record<string, string> = {
  OK: "#10B981", WARNING: "#F59E0B", CRITICAL: "#EF4444",
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Raccourci global Ctrl+K / Cmd+K.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) {
      setQ("");
      setResults(null);
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  // Recherche débouncée.
  useEffect(() => {
    if (q.trim().length < 2) {
      setResults(null);
      return;
    }
    const t = setTimeout(() => {
      globalSearch(q.trim()).then((r) => { setResults(r.data); setActive(0); }).catch(() => {});
    }, 220);
    return () => clearTimeout(t);
  }, [q]);

  const items = useMemo<Item[]>(() => {
    const out: Item[] = [];
    const needle = q.trim().toLowerCase();
    if (needle.length >= 1) {
      for (const p of PAGES.filter((p) => p.label.toLowerCase().includes(needle)).slice(0, 4)) {
        out.push({ key: `page-${p.to}`, icon: LayoutDashboard, title: p.label, group: "Pages", to: p.to });
      }
    }
    if (results) {
      for (const h of results.hosts) {
        out.push({ key: `h-${h.id}`, icon: Server, title: h.name, subtitle: h.hostname_or_ip, group: "Hôtes", to: `/hosts/${h.id}` });
      }
      for (const c of results.checks) {
        out.push({
          key: `c-${c.id}`, icon: ListChecks, title: c.name,
          subtitle: `${c.host_name} · ${c.type}`, group: "Checks", to: `/checks/${c.id}`,
          color: STATUS_COLOR[c.last_status ?? ""],
        });
      }
      for (const t of results.tickets) {
        out.push({ key: `t-${t.id}`, icon: Ticket, title: `#${t.id} ${t.title}`, subtitle: `${t.status} · ${t.priority}`, group: "Tickets", to: "/tickets" });
      }
      for (const e of results.events) {
        out.push({ key: `e-${e.id}`, icon: History, title: e.message.slice(0, 90), subtitle: e.level, group: "Événements", to: "/events" });
      }
    }
    return out;
  }, [q, results]);

  const go = useCallback((item: Item) => {
    setOpen(false);
    navigate(item.to);
  }, [navigate]);

  const onInputKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, items.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    if (e.key === "Enter" && items[active]) { e.preventDefault(); go(items[active]); }
  };

  let lastGroup = "";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -8 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl overflow-hidden rounded-2xl border border-border bg-bg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2.5 border-b border-border px-4">
              <Search className="h-4 w-4 shrink-0 text-ink-faint" />
              <input
                ref={inputRef}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={onInputKey}
                placeholder="Rechercher un hôte, check, ticket, événement, page…"
                className="w-full bg-transparent py-3.5 text-sm text-ink outline-none placeholder:text-ink-faint"
              />
              <kbd className="shrink-0 rounded border border-border bg-bg-soft px-1.5 py-0.5 text-[10px] text-ink-faint">Esc</kbd>
            </div>

            <div className="max-h-[50vh] overflow-y-auto p-2">
              {items.length === 0 ? (
                <p className="py-8 text-center text-sm text-ink-faint">
                  {q.trim().length < 2 ? "Tape au moins 2 caractères…" : "Aucun résultat."}
                </p>
              ) : (
                items.map((item, i) => {
                  const header = item.group !== lastGroup ? item.group : null;
                  lastGroup = item.group;
                  return (
                    <div key={item.key}>
                      {header && (
                        <p className="px-2 pb-1 pt-2.5 text-[10px] font-semibold uppercase tracking-wider text-ink-faint">
                          {header}
                        </p>
                      )}
                      <button
                        onClick={() => go(item)}
                        onMouseEnter={() => setActive(i)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left",
                          i === active ? "bg-brand/15" : "hover:bg-bg-soft",
                        )}
                      >
                        <item.icon className="h-4 w-4 shrink-0 text-ink-faint" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm text-ink">{item.title}</p>
                          {item.subtitle && <p className="truncate text-xs text-ink-faint">{item.subtitle}</p>}
                        </div>
                        {item.color && <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: item.color }} />}
                        {i === active && <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-ink-faint" />}
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex items-center gap-3 border-t border-border bg-bg-soft/40 px-4 py-2 text-[10px] text-ink-faint">
              <span>↑↓ naviguer</span><span>↵ ouvrir</span><span>Esc fermer</span>
              <span className="ml-auto flex items-center gap-1">Ctrl+K <ArrowRight className="h-3 w-3" /> recherche globale</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
