/** Internationalisation (FR/EN). Locale persistée en localStorage.
 *
 *  Usage :
 *    const { t, lang, setLang } = useI18n();
 *    <span>{t("nav.dashboard")}</span>
 *
 *  Les clés absentes retombent sur le français puis sur la clé brute — l'app
 *  reste donc fonctionnelle pendant la migration progressive des pages. */
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "fr" | "en";

const KEY = "opsora_lang";

export function getLang(): Lang {
  try {
    const l = localStorage.getItem(KEY);
    if (l === "fr" || l === "en") return l;
    // Défaut : langue du navigateur si anglais, sinon français.
    if (typeof navigator !== "undefined" && navigator.language?.toLowerCase().startsWith("en")) return "en";
  } catch { /* localStorage indisponible */ }
  return "fr";
}

/** Dictionnaire : { clé: { fr, en } }. Ajouter les clés au fil de la migration. */
const DICT: Record<string, { fr: string; en: string }> = {
  // Navigation (barre latérale)
  "nav.dashboard": { fr: "Dashboard", en: "Dashboard" },
  "nav.monitoring": { fr: "Monitoring", en: "Monitoring" },
  "nav.hosts": { fr: "Hôtes", en: "Hosts" },
  "nav.checks": { fr: "Checks", en: "Checks" },
  "nav.templates": { fr: "Templates", en: "Templates" },
  "nav.incidents": { fr: "Incidents", en: "Incidents" },
  "nav.tickets": { fr: "Tickets", en: "Tickets" },
  "nav.apm": { fr: "APM", en: "APM" },
  "nav.containers": { fr: "Conteneurs", en: "Containers" },
  "nav.topology": { fr: "Topologie", en: "Topology" },
  "nav.map": { fr: "Carte", en: "Map" },
  "nav.operations": { fr: "Opérations", en: "Operations" },
  "nav.business": { fr: "Métier", en: "Business" },
  "nav.reports": { fr: "Rapports", en: "Reports" },
  "nav.events": { fr: "Événements", en: "Events" },
  "nav.audit": { fr: "Audit", en: "Audit" },
  "nav.assistant": { fr: "Assistant", en: "Assistant" },
  "nav.knowledge": { fr: "Connaissances", en: "Knowledge" },
  "nav.tenants": { fr: "Tenants", en: "Tenants" },
  "nav.settings": { fr: "Paramètres", en: "Settings" },
  "nav.docs": { fr: "Documentation", en: "Documentation" },

  // Barre supérieure
  "topbar.tv": { fr: "Mode TV", en: "TV mode" },
  "topbar.search": { fr: "Rechercher…", en: "Search…" },
  "topbar.logout": { fr: "Déconnexion", en: "Sign out" },
  "topbar.collapse": { fr: "Réduire", en: "Collapse" },
  "topbar.expand": { fr: "Déplier", en: "Expand" },
  "theme.dark": { fr: "Sombre", en: "Dark" },
  "theme.light": { fr: "Clair", en: "Light" },
  "theme.system": { fr: "Système", en: "System" },
  "lang.switch": { fr: "Langue", en: "Language" },

  // Rôles
  "role.admin": { fr: "Administrateur", en: "Administrator" },
  "role.operator": { fr: "Opérateur", en: "Operator" },
  "role.viewer": { fr: "Lecture seule", en: "Read-only" },

  // Connexion
  "login.subtitle": { fr: "Plateforme de supervision", en: "Monitoring platform" },
  "login.email": { fr: "Email", en: "Email" },
  "login.password": { fr: "Mot de passe", en: "Password" },
  "login.forgot": { fr: "Mot de passe oublié ?", en: "Forgot password?" },
  "login.submit": { fr: "Se connecter", en: "Sign in" },
  "login.submitting": { fr: "Connexion...", en: "Signing in..." },
  "login.sso": { fr: "Connexion entreprise (SSO)", en: "Enterprise sign-in (SSO)" },
  "login.invalid": { fr: "Identifiants invalides", en: "Invalid credentials" },
  "login.enterEmailFirst": {
    fr: "Saisis d'abord ton e-mail, puis clique sur « Mot de passe oublié ».",
    en: "Enter your email first, then click “Forgot password”.",
  },
  "login.resetSent": {
    fr: "Si un compte existe, un e-mail de réinitialisation a été envoyé.",
    en: "If an account exists, a reset email has been sent.",
  },

  // Aide / documentation
  "common.help": { fr: "Aide", en: "Help" },
  "common.loading": { fr: "Chargement...", en: "Loading..." },
  "common.loadError": { fr: "Erreur de chargement", en: "Failed to load" },
  "common.save": { fr: "Enregistrer", en: "Save" },
  "common.cancel": { fr: "Annuler", en: "Cancel" },
  "common.create": { fr: "Créer", en: "Create" },
  "common.delete": { fr: "Supprimer", en: "Delete" },
  "common.edit": { fr: "Modifier", en: "Edit" },
  "common.add": { fr: "Ajouter", en: "Add" },
  "common.search": { fr: "Rechercher…", en: "Search…" },
  "common.test": { fr: "Tester", en: "Test" },
  "common.close": { fr: "Fermer", en: "Close" },
  "common.confirm": { fr: "Confirmer", en: "Confirm" },
  "common.name": { fr: "Nom", en: "Name" },
  "common.description": { fr: "Description", en: "Description" },
  "common.actions": { fr: "Actions", en: "Actions" },
  "common.all": { fr: "Tous", en: "All" },
  "common.none": { fr: "Aucun", en: "None" },
  "common.active": { fr: "actif", en: "active" },
  "common.inactive": { fr: "inactif", en: "inactive" },
  "common.env": { fr: "Env", en: "Env" },
  "common.uptime": { fr: "Uptime", en: "Uptime" },
  "common.checks": { fr: "Checks", en: "Checks" },
  "common.neverChecked": { fr: "jamais vérifié", en: "never checked" },

  // Dashboard
  "dash.subtitle": { fr: "Vue d'ensemble temps réel", en: "Real-time overview" },
  "dash.customize": { fr: "Personnaliser", en: "Customize" },
  "dash.customizeHint": { fr: "Réorganiser / masquer les sections", en: "Reorder / hide sections" },
  "dash.default": { fr: "Défaut", en: "Default" },
  "dash.defaultHint": { fr: "Revenir au dashboard par défaut", en: "Reset to the default dashboard" },
  "dash.moveUp": { fr: "Monter", en: "Move up" },
  "dash.moveDown": { fr: "Descendre", en: "Move down" },
  "dash.show": { fr: "Afficher", en: "Show" },
  "dash.hide": { fr: "Masquer", en: "Hide" },
  "dash.sec.hero": { fr: "État global & disponibilité", en: "Global state & availability" },
  "dash.sec.kpis": { fr: "Indicateurs clés", en: "Key indicators" },
  "dash.sec.incidents": { fr: "Incidents, répartition & live", en: "Incidents, breakdown & live" },
  "dash.sec.trend": { fr: "Tendance & résumé IA", en: "Trend & AI summary" },
  "dash.head.allOk": { fr: "Tous les systèmes opérationnels", en: "All systems operational" },
  "dash.head.critical": { fr: "Intervention requise", en: "Action required" },
  "dash.criticalServices": { fr: "service(s) critiques", en: "critical service(s)" },
  "dash.activeIncidents": { fr: "incident(s) actif(s)", en: "active incident(s)" },
  "dash.warningsOngoing": { fr: "avertissement(s) en cours", en: "warning(s) ongoing" },
  "dash.head.watch": { fr: "Points à surveiller", en: "Points to watch" },
  "dash.head.waiting": { fr: "En attente de données", en: "Waiting for data" },
  "dash.sub.noIncident": { fr: "Aucun incident actif — rien à signaler", en: "No active incident — nothing to report" },
  "dash.sub.noRecent": { fr: "Aucun résultat de check récent", en: "No recent check results" },
  "dash.proOnly": { fr: "Dashboards personnalisables : disponibles à partir du plan Professional.", en: "Customizable dashboards: available from the Professional plan." },
  "dash.hostsTotal": { fr: "Hôtes", en: "Hosts" },
  "dash.availability": { fr: "Disponibilité", en: "Availability" },
  "dash.hostsUp": { fr: "Hôtes UP", en: "Hosts UP" },
  "dash.hostsDown": { fr: "Hôtes DOWN", en: "Hosts DOWN" },
  "dash.stateBreakdown": { fr: "Répartition des états", en: "State breakdown" },
  "dash.trend24": { fr: "Tendance de disponibilité — 24 h", en: "Availability trend — 24 h" },
  "dash.handle": { fr: "Traiter", en: "Handle" },
  "dash.avail24": { fr: "Dispo 24 h", en: "24 h uptime" },
  "dash.last24": { fr: "sur les dernières 24 h", en: "over the last 24 h" },
  "dash.activeIncidentsTitle": { fr: "Incidents actifs", en: "Active incidents" },
  "dash.seeAll": { fr: "Voir tout →", en: "See all →" },
  "dash.allUnderControl": { fr: "Tout est sous contrôle 🎉", en: "Everything under control 🎉" },
  "dash.noIncidentNow": { fr: "Aucun incident actif en ce moment.", en: "No active incident right now." },
  "dash.checksTotal": { fr: "Checks", en: "Checks" },
  "dash.noHosts": { fr: "Aucun hôte enregistré.", en: "No host registered." },
  "dash.incidents": { fr: "Incidents", en: "Incidents" },

  // Hôtes
  "hosts.hostsSuffix": { fr: "hôtes", en: "hosts" },
  "hosts.supervised": { fr: "hôtes supervisés", en: "monitored hosts" },
  "hosts.discovery": { fr: "Découverte", en: "Discovery" },
  "hosts.import": { fr: "Importer", en: "Import" },
  "hosts.new": { fr: "Nouvel hôte", en: "New host" },
  "hosts.edit": { fr: "Modifier l'hôte", en: "Edit host" },
  "hosts.create": { fr: "Créer l'hôte", en: "Create host" },
  "hosts.confirmDelete": { fr: "Supprimer cet hôte ?", en: "Delete this host?" },
  "hosts.empty": { fr: "Aucun hôte.", en: "No host." },
  "hosts.searchPh": { fr: "Rechercher un hôte…", en: "Search a host…" },
  "hosts.f.hostnameIp": { fr: "Hostname ou IP", en: "Hostname or IP" },
  "hosts.f.environment": { fr: "Environnement", en: "Environment" },
  "hosts.f.site": { fr: "Site (ex. Agence Paris)", en: "Site (e.g. Paris Office)" },
  "hosts.f.lat": { fr: "Latitude (ex. 48.8566)", en: "Latitude (e.g. 48.8566)" },
  "hosts.f.lon": { fr: "Longitude (ex. 2.3522)", en: "Longitude (e.g. 2.3522)" },
  "hosts.f.mode": { fr: "Mode de supervision", en: "Supervision mode" },
  "hosts.mode.agentless": { fr: "Agentless (le serveur sonde l'hôte)", en: "Agentless (the server probes the host)" },
  "hosts.mode.agent": { fr: "Agent (push HTTPS depuis l'hôte)", en: "Agent (HTTPS push from the host)" },
  "hosts.mode.ssh": { fr: "SSH (tunnel, le serveur se connecte en SSH)", en: "SSH (tunnel, the server connects over SSH)" },
  "hosts.agentHint": { fr: "Après création, ouvrez la fiche de l'hôte : la carte « Superviser cet hôte » fournit la commande d'installation de l'agent (push HTTPS).", en: "After creation, open the host page: the “Monitor this host” card provides the agent install command (HTTPS push)." },
  "hosts.f.sshPort": { fr: "Port SSH (défaut 22)", en: "SSH port (default 22)" },
  "hosts.f.sshUser": { fr: "Utilisateur SSH", en: "SSH user" },
  "hosts.f.sshPassword": { fr: "Mot de passe SSH", en: "SSH password" },
  "hosts.f.parent": { fr: "Hôte parent (dépendance — si en panne, alertes des enfants supprimées)", en: "Parent host (dependency — if down, children alerts suppressed)" },
  "hosts.close": { fr: "fermer", en: "close" },

  // En-têtes de page (titre + sous-titre)
  "page.settings.title": { fr: "Paramètres", en: "Settings" },
  "page.settings.sub": { fr: "Canaux de notification, utilisateurs et préférences", en: "Notification channels, users and preferences" },
  "page.checks.title": { fr: "Checks", en: "Checks" },
  "page.checks.sub": { fr: "sondes configurées", en: "configured checks" },
  "page.monitoring.title": { fr: "Monitoring en direct", en: "Live Monitoring" },
  "page.monitoring.sub": { fr: "Flux d'événements et état de la flotte en temps réel", en: "Event stream and fleet state in real time" },
  "page.events.title": { fr: "Historique des événements", en: "Event history" },
  "page.events.sub": { fr: "Journal global : alertes, acquittements, maintenances, remédiations", en: "Global log: alerts, acknowledgments, maintenance, remediations" },
  "page.incidents.title": { fr: "Centre d'incidents", en: "Incident Center" },
  "page.incidents.sub": { fr: "Gestion centralisée des alertes actives", en: "Centralized management of active alerts" },
  "page.reports.title": { fr: "Rapports", en: "Reports" },
  "page.reports.sub": { fr: "Disponibilité agrégée — calculée à partir des résultats de checks réels", en: "Aggregated availability — computed from real check results" },
  "page.apm.title": { fr: "APM", en: "APM" },
  "page.apm.sub": { fr: "Supervision applicative — débit, erreurs et latence des applications", en: "Application monitoring — throughput, errors and latency" },
  "page.containers.title": { fr: "Conteneurs", en: "Containers" },
  "page.containers.sub": { fr: "Supervision Docker — état et ressources des conteneurs de l'hôte", en: "Docker monitoring — state and resources of the host's containers" },
  "page.tenants.title": { fr: "Tenants", en: "Tenants" },
  "page.tenants.sub": { fr: "Multi-tenant MSP — clients cloisonnés sur une seule instance", en: "Multi-tenant MSP — isolated customers on a single instance" },
  "page.templates.title": { fr: "Templates", en: "Templates" },
  "page.templates.sub": { fr: "Modèles de checks — appliquez un jeu de checks standard à un hôte en un clic", en: "Check templates — apply a standard check set to a host in one click" },
  "page.bam.title": { fr: "Métier", en: "Business" },
  "page.bam.sub": { fr: "Surveillance métier (BAM) — agrège des checks/hôtes avec une règle d'impact", en: "Business monitoring (BAM) — aggregates checks/hosts with an impact rule" },
  "page.audit.title": { fr: "Audit", en: "Audit" },
  "page.audit.sub": { fr: "Journal d'audit — qui a fait quoi, quand, depuis où (enregistrements immuables)", en: "Audit log — who did what, when, from where (immutable records)" },
  "page.topology.title": { fr: "Topologie réseau", en: "Network Topology" },
  "page.topology.sub": { fr: "Cartographie des hôtes par environnement — liens colorés selon l'état", en: "Host mapping by environment — links colored by state" },
  "page.geo.title": { fr: "Carte", en: "Map" },
  "page.geo.sub": { fr: "Vue géographique — place tes équipements d'un clic sur la carte", en: "Geographic view — place your devices on the map with one click" },
  "page.operations.title": { fr: "Opérations", en: "Operations" },
  "page.operations.sub": { fr: "Cartographie métier temps réel — glissez les tuiles pour composer votre carte", en: "Real-time business map — drag the tiles to compose your map" },
  "page.knowledge.title": { fr: "Connaissances", en: "Knowledge" },
  "page.knowledge.sub": { fr: "Base de connaissances (RAG) — l'assistant IA s'appuie sur vos runbooks pour répondre", en: "Knowledge base (RAG) — the AI assistant relies on your runbooks to answer" },
  "page.chat.title": { fr: "Assistant IA", en: "AI Assistant" },
  "page.chat.sub": { fr: "Questions en langage naturel sur l'état de la plateforme", en: "Natural-language questions about the platform state" },
  "page.tickets.title": { fr: "Tickets", en: "Tickets" },
  "page.tickets.sub": { fr: "Gestion des incidents ITSM — création, suivi et intégration externe", en: "ITSM incident management — creation, tracking and external integration" },

  // Événements
  "ev.type.alert_opened": { fr: "Alerte ouverte", en: "Alert opened" },
  "ev.type.alert_resolved": { fr: "Alerte résolue", en: "Alert resolved" },
  "ev.type.alert_suppressed": { fr: "Alerte supprimée (maintenance)", en: "Alert suppressed (maintenance)" },
  "ev.type.alert_acknowledged": { fr: "Incident acquitté", en: "Incident acknowledged" },
  "ev.type.alert_unacknowledged": { fr: "Acquittement retiré", en: "Acknowledgment removed" },
  "ev.type.maintenance_created": { fr: "Maintenance planifiée", en: "Maintenance scheduled" },
  "ev.type.maintenance_deleted": { fr: "Maintenance supprimée", en: "Maintenance deleted" },
  "ev.type.remediation": { fr: "Remédiation", en: "Remediation" },
  "ev.f.alerts": { fr: "Alertes", en: "Alerts" },
  "ev.f.acks": { fr: "Acquittements", en: "Acknowledgments" },
  "ev.f.maintenance": { fr: "Maintenances", en: "Maintenance" },
  "ev.f.remediation": { fr: "Remédiations", en: "Remediations" },
  "ev.searchPh": { fr: "Rechercher (hôte, message, utilisateur…)", en: "Search (host, message, user…)" },
  "ev.allLevels": { fr: "Tous niveaux", en: "All levels" },
  "ev.info": { fr: "Info", en: "Info" },
  "ev.warning": { fr: "Avertissement", en: "Warning" },
  "ev.critical": { fr: "Critique", en: "Critical" },
  "ev.noneMatch": { fr: "Aucun événement ne correspond à la recherche.", en: "No event matches the search." },
  "ev.none": { fr: "Aucun événement.", en: "No event." },
  "ev.loadMore": { fr: "Charger plus", en: "Load more" },

  // Paramètres
  "set.usersRoles": { fr: "Utilisateurs & rôles", en: "Users & roles" },
  "set.pwMin": { fr: "Mot de passe (min 6)", en: "Password (min 6)" },
  "set.pwConfirm": { fr: "Confirmer le mot de passe", en: "Confirm password" },
  "set.ownRole": { fr: "Vous ne pouvez pas changer votre propre rôle ici", en: "You cannot change your own role here" },
  "set.pwMismatch": { fr: "Les deux mots de passe ne correspondent pas.", en: "The two passwords do not match." },
  "set.createUserFail": { fr: "Création impossible (email déjà utilisé ou mot de passe trop court).", en: "Creation failed (email already used or password too short)." },
  "set.testSent": { fr: "Notification de test envoyée ✅", en: "Test notification sent ✅" },
  "set.testFail": { fr: "Échec de l'envoi — vérifie la configuration du canal (voir logs backend).", en: "Sending failed — check the channel configuration (see backend logs)." },
  "set.confirmDeleteUser": { fr: "Supprimer l'utilisateur", en: "Delete user" },
  "set.badJson": { fr: "config_json invalide", en: "invalid config_json" },
  "set.purgeDone": { fr: "Purge terminée", en: "Purge complete" },
  "set.rowsDeleted": { fr: "ligne(s) supprimée(s).", en: "row(s) deleted." },
  "set.dbRetention": { fr: "Base de données & rétention", en: "Database & retention" },
  "set.purging": { fr: "Purge...", en: "Purging..." },
  "set.purgeNow": { fr: "Purger maintenant", en: "Purge now" },
  "set.ret.checkResults": { fr: "Résultats de checks", en: "Check results" },
  "set.ret.metricsRaw": { fr: "Métriques (brut)", en: "Metrics (raw)" },
  "set.ret.metricsHourly": { fr: "Métriques (horaire)", en: "Metrics (hourly)" },
  "set.ret.alerts": { fr: "Alertes", en: "Alerts" },
  "set.retentionNote": { fr: "La purge automatique tourne via le scheduler ; les données au-delà de la fenêtre de rétention sont supprimées (configurable via variables d'environnement).", en: "Automatic purge runs via the scheduler; data beyond the retention window is deleted (configurable via environment variables)." },
  "set.channels": { fr: "Canaux de notification", en: "Notification channels" },
  "set.escalationOnly": { fr: "Escalade uniquement (astreinte)", en: "Escalation only (on-call)" },
  "set.activeHoursPh": { fr: "Plage horaire ex. 08:00-20:00 (vide = 24/7)", en: "Time window e.g. 08:00-20:00 (empty = 24/7)" },
  "set.addChannel": { fr: "Ajouter le canal", en: "Add channel" },
  "set.adminOnlyChannels": { fr: "Seul un administrateur peut configurer les canaux.", en: "Only an administrator can configure channels." },
  "set.noChannels": { fr: "Aucun canal configuré.", en: "No channel configured." },
  "set.onCall": { fr: "astreinte", en: "on-call" },
  "set.smtpNote": { fr: "SMTP et autres secrets sont configurés via variables d'environnement (voir .env).", en: "SMTP and other secrets are configured via environment variables (see .env)." },
  "set.retentionWord": { fr: "rétention", en: "retention" },
  "set.daysShort": { fr: "j", en: "d" },
  "set.oldest": { fr: "plus ancien", en: "oldest" },
  // Compte
  "acc.title": { fr: "Mon compte", en: "My account" },
  "acc.connectedAs": { fr: "Connecté en tant que", en: "Signed in as" },
  "acc.currentPw": { fr: "Mot de passe actuel", en: "Current password" },
  "acc.newPw": { fr: "Nouveau mot de passe", en: "New password" },
  "acc.confirmNew": { fr: "Confirmer le nouveau", en: "Confirm the new one" },
  "acc.changeMyPw": { fr: "Changer mon mot de passe", en: "Change my password" },
  "acc.pwMismatch": { fr: "Les deux mots de passe ne correspondent pas.", en: "The two passwords do not match." },
  "acc.pwTooShort": { fr: "Le mot de passe doit faire au moins 6 caractères.", en: "The password must be at least 6 characters." },
  "acc.pwChanged": { fr: "Mot de passe modifié ✅", en: "Password changed ✅" },
  "acc.changeFail": { fr: "Modification impossible.", en: "Change failed." },
  // Rôles personnalisés
  "roles.title": { fr: "Rôles personnalisés", en: "Custom roles" },
  "roles.intro": { fr: "Créez un profil avec des droits de modification à la carte. La lecture reste ouverte à tout compte ; les cases cochées autorisent la création / modification / suppression dans la section.", en: "Create a profile with à-la-carte edit rights. Read access stays open to any account; ticked boxes allow create / edit / delete in the section." },
  "roles.namePh": { fr: "Nom du rôle (ex. superviseur-réseau)", en: "Role name (e.g. network-supervisor)" },
  "roles.descPh": { fr: "Description (optionnel)", en: "Description (optional)" },
  "roles.saveFail": { fr: "Enregistrement impossible.", en: "Save failed." },
  "roles.confirmDelete": { fr: "Supprimer le rôle", en: "Delete role" },
  "roles.confirmDeleteTail": { fr: "? Les utilisateurs concernés repasseront en lecture seule.", en: "? The affected users will revert to read-only." },
  "roles.createRole": { fr: "Créer le rôle", en: "Create role" },
  "roles.none": { fr: "Aucun rôle personnalisé pour l'instant.", en: "No custom role yet." },
  "roles.readOnly": { fr: "Lecture seule", en: "Read-only" },

  // Incidents
  "inc.totalActive": { fr: "Total actifs", en: "Total active" },
  "inc.acked": { fr: "Acquittés", en: "Acknowledged" },
  "inc.searchPh": { fr: "Rechercher (hôte, check, message)…", en: "Search (host, check, message)…" },
  "inc.noneMatch": { fr: "Aucun incident ne correspond 🎉", en: "No incident matches 🎉" },
  "inc.analysisFailed": { fr: "Analyse impossible (IA injoignable ?).", en: "Analysis failed (AI unreachable?)." },
  "inc.waitingAgent": { fr: "⏳ En attente de l'agent…", en: "⏳ Waiting for the agent…" },
  "inc.noResult": { fr: "(aucun résultat)", en: "(no result)" },
  "inc.agentNoReply": { fr: "L'agent n'a pas répondu (hors ligne ?).", en: "The agent did not respond (offline?)." },
  "inc.actionFailed": { fr: "Action impossible.", en: "Action failed." },

  // Statuts (état global)
  "topbar.platform": { fr: "Plateforme", en: "Platform" },
  "status.OK": { fr: "Opérationnel", en: "Operational" },
  "status.WARNING": { fr: "Avertissement", en: "Warning" },
  "status.CRITICAL": { fr: "Critique", en: "Critical" },
  "status.UNKNOWN": { fr: "Inconnu", en: "Unknown" },
};

export function translate(lang: Lang, key: string): string {
  const entry = DICT[key];
  if (!entry) return key;
  return entry[lang] ?? entry.fr ?? key;
}

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getLang);

  useEffect(() => {
    try { document.documentElement.lang = lang; } catch { /* ignore */ }
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try { localStorage.setItem(KEY, l); } catch { /* ignore */ }
  }, []);

  const t = useCallback((key: string) => translate(lang, key), [lang]);

  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
