/** Métadonnées par type de check : nom lisible, description, exemple de config.
 *  Sert à clarifier le formulaire de création (aide contextuelle + auto-remplissage). */
export interface CheckMeta {
  label: string;        // nom lisible dans le menu
  desc: string;         // ce que le check vérifie
  config: string;       // exemple de config_json (JSON string) — auto-rempli
  thresholds?: string;  // à quoi servent warn/crit (si applicable)
}

export const CHECK_META: Record<string, CheckMeta> = {
  ping: { label: "Ping (ICMP)", desc: "Vérifie que l'équipement répond au ping.", config: "{}" },
  tcp_port: { label: "Port TCP", desc: "Vérifie qu'un port TCP est ouvert.", config: '{"port": 443}' },
  http: { label: "HTTP / HTTPS", desc: "Interroge une URL (code HTTP, latence, contenu).", config: '{"scheme": "https", "path": "/", "expect": ""}', thresholds: "latence (ms)" },
  ssl_expiry: { label: "Certificat SSL", desc: "Alerte avant l'expiration du certificat.", config: '{"port": 443}', thresholds: "jours restants (warn 30 / crit 7)" },
  dns: { label: "DNS", desc: "Vérifie la résolution d'un nom.", config: '{"record": "A", "expect": ""}' },
  ntp: { label: "NTP (horloge)", desc: "Mesure la dérive d'horloge d'un serveur de temps.", config: '{"port": 123}', thresholds: "dérive en ms (warn 100 / crit 1000)" },
  snmp: { label: "SNMP (OID)", desc: "Interroge un OID SNMP (CPU, uptime, capteur…).", config: '{"metric": "cpu", "community": "public", "version": "2c"}', thresholds: "valeur numérique (ex. CPU %)" },
  snmp_traffic: { label: "SNMP trafic (interface)", desc: "Débit et erreurs d'une interface réseau.", config: '{"if_index": 1, "community": "public", "version": "2c"}' },
  ssh: { label: "SSH", desc: "Vérifie la connexion SSH (port + authentification).", config: '{"port": 22, "user": "", "password": ""}' },
  ssh_command: { label: "Commande SSH", desc: "Exécute une commande distante (métrique sur mesure).", config: '{"user": "", "password": "", "command": "uptime", "expect": ""}' },
  smtp: { label: "SMTP (e-mail)", desc: "Vérifie un serveur d'envoi d'e-mails.", config: '{"port": 25, "tls": false}' },
  imap: { label: "IMAP", desc: "Vérifie un serveur de réception IMAP.", config: '{"port": 993, "tls": true}' },
  pop3: { label: "POP3", desc: "Vérifie un serveur de réception POP3.", config: '{"port": 995, "tls": true}' },
  ftp: { label: "FTP", desc: "Vérifie un serveur FTP.", config: '{"port": 21}' },
  ldap: { label: "LDAP / AD", desc: "Vérifie un annuaire LDAP/Active Directory.", config: '{"port": 389, "base_dn": ""}' },
  database: { label: "Base de données", desc: "Connexion + requête sur PostgreSQL, MySQL, Oracle ou SQL Server.", config: '{"engine": "postgresql", "port": 5432, "user": "", "password": "", "dbname": "", "query": "SELECT 1"}', thresholds: "temps de réponse (ms)" },
  metric: { label: "Métrique agent", desc: "Seuil sur une métrique poussée par l'agent (CPU/RAM/disque…).", config: '{"metric": "cpu_percent"}', thresholds: "valeur % (warn 80 / crit 90)" },
  windows_service: { label: "Service Windows", desc: "État d'un service Windows (via agent).", config: '{"service": "Spooler"}' },
  disk_usage: { label: "Disque (serveur central)", desc: "Utilisation disque du serveur de supervision.", config: "{}", thresholds: "% utilisé" },
  cpu_load: { label: "Charge CPU (serveur central)", desc: "Charge CPU du serveur de supervision.", config: "{}", thresholds: "charge" },
  apm: { label: "APM (application)", desc: "Taux d'erreur / latence / débit d'une application.", config: '{"app": "mon-app", "metric": "error_rate", "window_minutes": 15}', thresholds: "selon la métrique" },
  docker: { label: "Docker (conteneurs)", desc: "Flotte entière (vide) ou un conteneur précis.", config: '{"container": ""}', thresholds: "CPU % du conteneur" },
  kubernetes: { label: "Kubernetes", desc: "Nodes / pods d'un namespace / deployment.", config: '{"api_url": "https://cluster:6443", "token": "", "mode": "nodes", "namespace": "default"}' },
  proxmox: { label: "Proxmox VE", desc: "Cluster / VM+CT d'un node / une VM.", config: '{"api_url": "https://pve:8006", "token_id": "user@pve!id", "token_secret": "", "mode": "cluster"}' },
  vmware: { label: "VMware vSphere", desc: "Hôtes ESXi / VMs / une VM.", config: '{"api_url": "https://vcenter", "user": "", "password": "", "mode": "hosts"}' },
  ipmi: { label: "IPMI / Redfish", desc: "Santé matérielle (iDRAC, iLO…) : ventilateurs, alims, RAID.", config: '{"api_url": "https://idrac", "user": "", "password": ""}' },
};

export function metaFor(type: string): CheckMeta {
  return CHECK_META[type] ?? { label: type, desc: "", config: "{}" };
}
