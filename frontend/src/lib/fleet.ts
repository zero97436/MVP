import type { Check, Host } from "../types";
import { worstStatus } from "./status";
import type { HostView } from "../components/ui/HostCard";

/** Combine hôtes + checks pour produire des HostView avec statut agrégé. */
export function buildHostViews(hosts: Host[], checks: Check[]): HostView[] {
  const byHost = new Map<number, Check[]>();
  for (const c of checks) {
    const arr = byHost.get(c.host_id) ?? [];
    arr.push(c);
    byHost.set(c.host_id, arr);
  }
  return hosts.map((h) => {
    const hc = byHost.get(h.id) ?? [];
    return {
      ...h,
      status: worstStatus(hc.map((c) => c.last_status)),
      checksCount: hc.length,
      lastCheckAt: h.updated_at,
    };
  });
}
