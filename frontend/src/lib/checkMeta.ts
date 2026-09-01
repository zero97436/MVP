/** Métadonnées par type de check : nom lisible, description, exemple de config.
 *  Sert à clarifier le formulaire de création (aide contextuelle + auto-remplissage).
 *  Bilingue (FR/EN) : `config` est neutre ; label/desc/thresholds sont traduits. */
export interface CheckMeta {
  label: string;        // nom lisible dans le menu
  desc: string;         // ce que le check vérifie
  config: string;       // exemple de config_json (JSON string) — auto-rempli
  thresholds?: string;  // à quoi servent warn/crit (si applicable)
}

type Lang = "fr" | "en";

interface CheckMetaI18n {
  label: string;
  config: string;
  desc: { fr: string; en: string };
  thresholds?: { fr: string; en: string };
}

const META: Record<string, CheckMetaI18n> = {
  ping: { label: "Ping (ICMP)", config: "{}", desc: { fr: "Vérifie que l'équipement répond au ping.", en: "Checks that the device responds to ping." } },
  tcp_port: { label: "Port TCP", config: '{"port": 443}', desc: { fr: "Vérifie qu'un port TCP est ouvert.", en: "Checks that a TCP port is open." } },
  http: { label: "HTTP / HTTPS", config: '{"scheme": "https", "path": "/", "expect": ""}', desc: { fr: "Interroge une URL (code HTTP, latence, contenu).", en: "Queries a URL (HTTP status, latency, content)." }, thresholds: { fr: "latence (ms)", en: "latency (ms)" } },
  ssl_expiry: { label: "Certificat SSL", config: '{"port": 443}', desc: { fr: "Alerte avant l'expiration du certificat.", en: "Alerts before the certificate expires." }, thresholds: { fr: "jours restants (warn 30 / crit 7)", en: "days remaining (warn 30 / crit 7)" } },
  dns: { label: "DNS", config: '{"record": "A", "expect": ""}', desc: { fr: "Vérifie la résolution d'un nom.", en: "Checks name resolution." } },
  ntp: { label: "NTP (horloge)", config: '{"port": 123}', desc: { fr: "Mesure la dérive d'horloge d'un serveur de temps.", en: "Measures clock drift of a time server." }, thresholds: { fr: "dérive en ms (warn 100 / crit 1000)", en: "drift in ms (warn 100 / crit 1000)" } },
  snmp: { label: "SNMP (OID)", config: '{"metric": "cpu", "community": "public", "version": "2c"}', desc: { fr: "Interroge un OID SNMP (CPU, uptime, capteur…).", en: "Queries an SNMP OID (CPU, uptime, sensor…)." }, thresholds: { fr: "valeur numérique (ex. CPU %)", en: "numeric value (e.g. CPU %)" } },
  snmp_traffic: { label: "SNMP trafic (interface)", config: '{"if_index": 1, "community": "public", "version": "2c"}', desc: { fr: "Débit et erreurs d'une interface réseau.", en: "Throughput and errors of a network interface." } },
  ssh: { label: "SSH", config: '{"port": 22, "user": "", "password": ""}', desc: { fr: "Vérifie la connexion SSH (port + authentification).", en: "Checks the SSH connection (port + authentication)." } },
  ssh_command: { label: "Commande SSH", config: '{"user": "", "password": "", "command": "uptime", "expect": ""}', desc: { fr: "Exécute une commande distante (métrique sur mesure).", en: "Runs a remote command (custom metric)." } },
  smtp: { label: "SMTP (e-mail)", config: '{"port": 25, "tls": false}', desc: { fr: "Vérifie un serveur d'envoi d'e-mails.", en: "Checks an outgoing mail server." } },
  imap: { label: "IMAP", config: '{"port": 993, "tls": true}', desc: { fr: "Vérifie un serveur de réception IMAP.", en: "Checks an IMAP mail server." } },
  pop3: { label: "POP3", config: '{"port": 995, "tls": true}', desc: { fr: "Vérifie un serveur de réception POP3.", en: "Checks a POP3 mail server." } },
  ftp: { label: "FTP", config: '{"port": 21}', desc: { fr: "Vérifie un serveur FTP.", en: "Checks an FTP server." } },
  ldap: { label: "LDAP / AD", config: '{"port": 389, "base_dn": ""}', desc: { fr: "Vérifie un annuaire LDAP/Active Directory.", en: "Checks an LDAP/Active Directory directory." } },
  database: { label: "Base de données", config: '{"engine": "postgresql", "port": 5432, "user": "", "password": "", "dbname": "", "query": "SELECT 1"}', desc: { fr: "Connexion + requête sur PostgreSQL, MySQL, Oracle ou SQL Server.", en: "Connection + query on PostgreSQL, MySQL, Oracle or SQL Server." }, thresholds: { fr: "temps de réponse (ms)", en: "response time (ms)" } },
  metric: { label: "Métrique agent", config: '{"metric": "cpu_percent"}', desc: { fr: "Seuil sur une métrique poussée par l'agent (CPU/RAM/disque…).", en: "Threshold on a metric pushed by the agent (CPU/RAM/disk…)." }, thresholds: { fr: "valeur % (warn 80 / crit 90)", en: "value % (warn 80 / crit 90)" } },
  windows_service: { label: "Service Windows", config: '{"service": "Spooler"}', desc: { fr: "État d'un service Windows (via agent).", en: "State of a Windows service (via agent)." } },
  disk_usage: { label: "Disque (serveur central)", config: "{}", desc: { fr: "Utilisation disque du serveur de supervision.", en: "Disk usage of the monitoring server." }, thresholds: { fr: "% utilisé", en: "% used" } },
  cpu_load: { label: "Charge CPU (serveur central)", config: "{}", desc: { fr: "Charge CPU du serveur de supervision.", en: "CPU load of the monitoring server." }, thresholds: { fr: "charge", en: "load" } },
  apm: { label: "APM (application)", config: '{"app": "mon-app", "metric": "error_rate", "window_minutes": 15}', desc: { fr: "Taux d'erreur / latence / débit d'une application.", en: "Error rate / latency / throughput of an application." }, thresholds: { fr: "selon la métrique", en: "depends on the metric" } },
  docker: { label: "Docker (conteneurs)", config: '{"container": ""}', desc: { fr: "Flotte entière (vide) ou un conteneur précis.", en: "Whole fleet (empty) or a specific container." }, thresholds: { fr: "CPU % du conteneur", en: "container CPU %" } },
  kubernetes: { label: "Kubernetes", config: '{"api_url": "https://cluster:6443", "token": "", "mode": "nodes", "namespace": "default"}', desc: { fr: "Nodes / pods d'un namespace / deployment.", en: "Nodes / pods of a namespace / deployment." } },
  proxmox: { label: "Proxmox VE", config: '{"api_url": "https://pve:8006", "token_id": "user@pve!id", "token_secret": "", "mode": "cluster"}', desc: { fr: "Cluster / VM+CT d'un node / une VM.", en: "Cluster / VM+CT of a node / a VM." } },
  vmware: { label: "VMware vSphere", config: '{"api_url": "https://vcenter", "user": "", "password": "", "mode": "hosts"}', desc: { fr: "Hôtes ESXi / VMs / une VM.", en: "ESXi hosts / VMs / a VM." } },
  ipmi: { label: "IPMI / Redfish", config: '{"api_url": "https://idrac", "user": "", "password": ""}', desc: { fr: "Santé matérielle (iDRAC, iLO…) : ventilateurs, alims, RAID.", en: "Hardware health (iDRAC, iLO…): fans, PSUs, RAID." } },
};

/** Compat : catalogue des exemples de config (indépendant de la langue). */
export const CHECK_META: Record<string, { config: string }> = Object.fromEntries(
  Object.entries(META).map(([k, m]) => [k, { config: m.config }]),
);

export function metaFor(type: string, lang: Lang = "fr"): CheckMeta {
  const m = META[type];
  if (!m) return { label: type, desc: "", config: "{}" };
  return {
    label: m.label,
    desc: m.desc[lang] ?? m.desc.fr,
    config: m.config,
    thresholds: m.thresholds ? (m.thresholds[lang] ?? m.thresholds.fr) : undefined,
  };
}
