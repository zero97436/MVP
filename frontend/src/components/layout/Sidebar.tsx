import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Activity,
  Server,
  ListChecks,
  LayoutTemplate,
  AlertTriangle,
  Share2,
  MapPin,
  Briefcase,
  LayoutGrid,
  FileBarChart,
  Ticket,
  Rocket,
  Container,
  History,
  ShieldCheck,
  Bot,
  BookOpen,
  LifeBuoy,
  Settings,
  Building2,
  ChevronLeft,
  type LucideIcon,
} from "lucide-react";
import { cn } from "../../lib/cn";
import { BrandLogo } from "../ui/BrandLogo";
import { useBranding } from "../../lib/branding";
import { useI18n } from "../../lib/i18n";

interface NavItem {
  to: string;
  labelKey: string;
  icon: LucideIcon;
}

const NAV: NavItem[] = [
  { to: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/monitoring", labelKey: "nav.monitoring", icon: Activity },
  { to: "/hosts", labelKey: "nav.hosts", icon: Server },
  { to: "/checks", labelKey: "nav.checks", icon: ListChecks },
  { to: "/templates", labelKey: "nav.templates", icon: LayoutTemplate },
  { to: "/incidents", labelKey: "nav.incidents", icon: AlertTriangle },
  { to: "/tickets", labelKey: "nav.tickets", icon: Ticket },
  { to: "/apm", labelKey: "nav.apm", icon: Rocket },
  { to: "/containers", labelKey: "nav.containers", icon: Container },
  { to: "/topology", labelKey: "nav.topology", icon: Share2 },
  { to: "/geo", labelKey: "nav.map", icon: MapPin },
  { to: "/operations", labelKey: "nav.operations", icon: LayoutGrid },
  { to: "/bam", labelKey: "nav.business", icon: Briefcase },
  { to: "/reports", labelKey: "nav.reports", icon: FileBarChart },
  { to: "/events", labelKey: "nav.events", icon: History },
  { to: "/audit", labelKey: "nav.audit", icon: ShieldCheck },
  { to: "/assistant", labelKey: "nav.assistant", icon: Bot },
  { to: "/knowledge", labelKey: "nav.knowledge", icon: BookOpen },
  { to: "/tenants", labelKey: "nav.tenants", icon: Building2 },
  { to: "/settings", labelKey: "nav.settings", icon: Settings },
  { to: "/docs", labelKey: "nav.docs", icon: LifeBuoy },
];

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const { branding } = useBranding();
  const { t } = useI18n();
  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      className="relative z-20 flex shrink-0 flex-col border-r border-border bg-bg-soft"
    >
      <div className="flex h-14 items-center gap-2 px-4">
        <BrandLogo className="h-8 w-8" />
        {!collapsed && (
          <span className="truncate text-sm font-semibold tracking-tight text-ink">
            {branding.display_name}
          </span>
        )}
      </div>

      <nav className="mt-2 flex-1 space-y-1 px-3">
        {NAV.map((item) => {
          const Icon = item.icon;
          const label = t(item.labelKey);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-brand/15 text-brand"
                    : "text-ink-soft hover:bg-card hover:text-ink",
                )
              }
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          );
        })}
      </nav>

      <button
        onClick={onToggle}
        className="m-3 flex items-center justify-center rounded-lg border border-border py-2 text-ink-faint transition hover:text-ink"
        title={collapsed ? t("topbar.expand") : t("topbar.collapse")}
      >
        <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
      </button>
    </motion.aside>
  );
}
