import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "../CommandPalette";
import { usePolling } from "../../hooks/usePolling";
import { getSummary } from "../../api/endpoints";
import type { CheckStatus, DashboardSummary } from "../../types";

const STORAGE_KEY = "sh_sidebar_collapsed";

function globalStatusFrom(s: DashboardSummary | null): CheckStatus {
  if (!s) return "UNKNOWN";
  const c = s.status_counts;
  if ((c.CRITICAL ?? 0) > 0) return "CRITICAL";
  if ((c.WARNING ?? 0) > 0) return "WARNING";
  if ((c.OK ?? 0) > 0) return "OK";
  return "UNKNOWN";
}

export function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(STORAGE_KEY) === "1");
  const location = useLocation();
  const { data: summary } = usePolling(() => getSummary().then((r) => r.data), 20000);

  const toggle = () => {
    setCollapsed((c) => {
      localStorage.setItem(STORAGE_KEY, c ? "0" : "1");
      return !c;
    });
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg text-ink">
      <CommandPalette />
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar globalStatus={globalStatusFrom(summary)} />
        <main className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
