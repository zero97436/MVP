export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso;
  }
}

/** "il y a 3 min" — relatif et compact. */
export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diff = Math.max(0, Date.now() - then);
  const s = Math.floor(diff / 1000);
  if (s < 60) return `il y a ${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `il y a ${h} h`;
  const d = Math.floor(h / 24);
  return `il y a ${d} j`;
}

/** Durée lisible à partir d'une date de départ (uptime). */
export function uptimeSince(iso: string): string {
  const start = new Date(iso).getTime();
  if (Number.isNaN(start)) return "—";
  const sec = Math.max(0, Math.floor((Date.now() - start) / 1000));
  const d = Math.floor(sec / 86400);
  const h = Math.floor((sec % 86400) / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (d > 0) return `${d}j ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function formatPercent(n: number, digits = 2): string {
  return `${n.toFixed(digits)}%`;
}

export function formatMs(ms?: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export const CHECK_TYPES = [
  "ping",
  "tcp_port",
  "http",
  "disk_usage",
  "cpu_load",
  "ssl_expiry",
  "metric",
  "snmp",
  "dns",
  "ssh",
  "smtp",
  "ftp",
  "database",
  "ssh_command",
  "imap",
  "pop3",
  "ldap",
  "snmp_traffic",
  "windows_service",
  "apm",
  "docker",
  "kubernetes",
  "proxmox",
  "vmware",
  "ipmi",
  "ntp",
] as const;
