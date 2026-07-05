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
  Bot,
  Settings,
  ChevronLeft,
  type LucideIcon,
} from "lucide-react";
import { cn } from "../../lib/cn";
import { BrandLogo } from "../ui/BrandLogo";
import { useBranding } from "../../lib/branding";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/monitoring", label: "Monitoring", icon: Activity },
  { to: "/hosts", label: "Hosts", icon: Server },
  { to: "/checks", label: "Checks", icon: ListChecks },
  { to: "/templates", label: "Templates", icon: LayoutTemplate },
  { to: "/incidents", label: "Incidents", icon: AlertTriangle },
  { to: "/tickets", label: "Tickets", icon: Ticket },
  { to: "/apm", label: "APM", icon: Rocket },
  { to: "/containers", label: "Conteneurs", icon: Container },
  { to: "/topology", label: "Topology", icon: Share2 },
  { to: "/geo", label: "Carte", icon: MapPin },
  { to: "/operations", label: "Opérations", icon: LayoutGrid },
  { to: "/bam", label: "Métier", icon: Briefcase },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/events", label: "Événements", icon: History },
  { to: "/assistant", label: "Assistant", icon: Bot },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const { branding } = useBranding();
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
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
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
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      <button
        onClick={onToggle}
        className="m-3 flex items-center justify-center rounded-lg border border-border py-2 text-ink-faint transition hover:text-ink"
        title={collapsed ? "Déplier" : "Réduire"}
      >
        <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
      </button>
    </motion.aside>
  );
}
