export type CheckStatus = "OK" | "WARNING" | "CRITICAL" | "UNKNOWN";

export type CheckType =
  | "ping"
  | "tcp_port"
  | "http"
  | "disk_usage"
  | "cpu_load"
  | "ssl_expiry"
  | "metric"
  | "snmp"
  | "dns"
  | "ssh"
  | "smtp"
  | "ftp"
  | "database"
  | "ssh_command"
  | "imap"
  | "pop3"
  | "ldap"
  | "snmp_traffic"
  | "windows_service"
  | "apm"
  | "docker"
  | "kubernetes"
  | "proxmox"
  | "vmware"
  | "ipmi"
  | "ntp";

export type UserRole = "admin" | "operator" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  is_admin: boolean;
  role: UserRole;
  is_active?: boolean;
  created_at?: string;
}

export interface Host {
  id: number;
  name: string;
  hostname_or_ip: string;
  description?: string | null;
  environment: string;
  is_active: boolean;
  parent_host_id?: number | null;
  location?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Check {
  id: number;
  host_id: number;
  name: string;
  type: CheckType;
  interval_seconds: number;
  timeout_seconds: number;
  warning_threshold?: number | null;
  critical_threshold?: number | null;
  config_json: Record<string, unknown>;
  is_active: boolean;
  last_status?: CheckStatus | null;
  executor_host_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface CheckResult {
  id: number;
  check_id: number;
  status: CheckStatus;
  value?: number | null;
  message?: string | null;
  perfdata: Record<string, unknown>;
  duration_ms?: number | null;
  checked_at: string;
}

export interface DashboardSummary {
  hosts_total: number;
  checks_total: number;
  status_counts: Record<CheckStatus, number>;
}

export interface Incident {
  alert_id: number;
  check_id: number;
  check_name: string;
  host_id: number;
  host_name: string;
  status: CheckStatus;
  message?: string | null;
  since: string;
  acknowledged: boolean;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
}

export interface HostMetric {
  id: number;
  host_id: number;
  cpu_percent?: number | null;
  mem_percent?: number | null;
  disk_percent?: number | null;
  disks?: Record<string, number> | null;
  net_mbps?: number | null;
  process_count?: number | null;
  load1?: number | null;
  temperature?: number | null;
  collected_at: string;
}

export interface HostMetricHourly {
  host_id: number;
  bucket: string;
  cpu_avg?: number | null;
  cpu_max?: number | null;
  mem_avg?: number | null;
  mem_max?: number | null;
  disk_avg?: number | null;
  disk_max?: number | null;
  net_avg?: number | null;
  net_max?: number | null;
  sample_count: number;
}

export interface EventLog {
  id: number;
  type: string;
  level: "info" | "warning" | "critical";
  message: string;
  host_id?: number | null;
  check_id?: number | null;
  actor?: string | null;
  created_at: string;
}

export interface Maintenance {
  id: number;
  host_id?: number | null;
  check_id?: number | null;
  reason?: string | null;
  starts_at: string;
  ends_at: string;
  created_by?: string | null;
  created_at: string;
}

export interface NotificationChannel {
  id: number;
  name: string;
  type: "email" | "webhook" | "slack" | "telegram" | "teams" | "discord" | "sms" | "script";
  config_json: Record<string, unknown>;
  escalation_only?: boolean;
  active_hours?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
