/** Contenu de la documentation intégrée, bilingue (FR/EN), structuré par section.
 *  Chaque entrée est ancrée sur `id` (ex. /docs#hosts) et référencée depuis
 *  l'en-tête de la page correspondante via <PageHeader helpTopic="hosts" />. */
import type { Lang } from "./i18n";

export interface DocSection {
  id: string;
  title: string;
  summary: string;
  body: string[];
  tips?: string[];
}

type LS = { fr: string; en: string };
interface DocSectionI18n {
  id: string;
  title: LS;
  summary: LS;
  body: LS[];
  tips?: LS[];
}

const SECTIONS: DocSectionI18n[] = [
  {
    id: "dashboard",
    title: { fr: "Dashboard", en: "Dashboard" },
    summary: { fr: "Vue d'ensemble temps réel de l'état du parc.", en: "Real-time overview of the fleet's state." },
    body: [
      { fr: "Le Dashboard agrège l'état de tous les hôtes et checks : compteurs UP/DOWN, OK/Warning/Critical, incidents en cours et tendances récentes.", en: "The Dashboard aggregates the state of all hosts and checks: UP/DOWN counters, OK/Warning/Critical, ongoing incidents and recent trends." },
      { fr: "Chaque indicateur (KPI) est cliquable et renvoie vers la liste filtrée correspondante : cliquez sur « Critical » pour ouvrir les incidents critiques, sur « DOWN » pour les hôtes injoignables, etc.", en: "Each indicator (KPI) is clickable and takes you to the matching filtered list: click “Critical” to open critical incidents, “DOWN” for unreachable hosts, and so on." },
    ],
    tips: [
      { fr: "Un résumé rédigé par l'IA peut synthétiser la situation si l'intégration Ollama est active.", en: "An AI-written summary can synthesize the situation if the Ollama integration is active." },
    ],
  },
  {
    id: "hosts",
    title: { fr: "Hôtes", en: "Hosts" },
    summary: { fr: "Équipements et serveurs supervisés, et leur mode de supervision.", en: "Monitored devices and servers, and their supervision mode." },
    body: [
      { fr: "Un hôte représente une machine ou un équipement (serveur, switch, routeur, sonde…). Créez-le avec son nom, son IP/hostname et son environnement.", en: "A host represents a machine or a device (server, switch, router, probe…). Create it with its name, IP/hostname and environment." },
      { fr: "Le champ « Mode de supervision » détermine comment Orbisys collecte l'état de l'hôte :", en: "The “Supervision mode” field determines how Orbisys collects the host's state:" },
      { fr: "• Agentless — le serveur sonde directement l'hôte sur le réseau (ICMP, SNMP, HTTP, TCP…). C'est le mode par défaut, sans rien à installer.", en: "• Agentless — the server probes the host directly over the network (ICMP, SNMP, HTTP, TCP…). This is the default mode, with nothing to install." },
      { fr: "• Agent (push HTTPS) — un agent léger installé sur l'hôte pousse ses métriques et résultats vers Orbisys. Après création, la fiche de l'hôte affiche la commande d'installation prête à copier.", en: "• Agent (HTTPS push) — a lightweight agent installed on the host pushes its metrics and results to Orbisys. After creation, the host page shows a ready-to-copy install command." },
      { fr: "• SSH (tunnel) — le serveur se connecte en SSH pour exécuter les checks. Renseignez le port, l'utilisateur et le mot de passe : les checks de l'hôte réutilisent automatiquement ces identifiants.", en: "• SSH (tunnel) — the server connects over SSH to run the checks. Provide the port, user and password: the host's checks automatically reuse these credentials." },
      { fr: "La dépendance « hôte parent » permet de supprimer les fausses alertes : si un switch amont tombe, les hôtes situés derrière sont marqués injoignables plutôt qu'en panne.", en: "The “parent host” dependency suppresses false alerts: if an upstream switch goes down, the hosts behind it are marked unreachable rather than down." },
    ],
    tips: [
      { fr: "Le mot de passe SSH est chiffré au repos et n'est jamais réaffiché en clair.", en: "The SSH password is encrypted at rest and never shown again in clear text." },
      { fr: "La commande d'installation de l'agent (mode agent) est réservée aux administrateurs car elle contient la clé d'ingestion.", en: "The agent install command (agent mode) is reserved for administrators because it contains the ingest key." },
    ],
  },
  {
    id: "checks",
    title: { fr: "Checks", en: "Checks" },
    summary: { fr: "Tests unitaires exécutés périodiquement sur un hôte.", en: "Unit tests run periodically against a host." },
    body: [
      { fr: "Un check est une vérification récurrente (ping, port TCP, HTTP, SNMP, espace disque, service Windows, requête SQL…). Choisissez le type : le formulaire affiche alors une aide contextuelle et pré-remplit un exemple de configuration.", en: "A check is a recurring verification (ping, TCP port, HTTP, SNMP, disk space, Windows service, SQL query…). Pick the type: the form then shows contextual help and pre-fills a configuration example." },
      { fr: "Réglez l'intervalle (fréquence d'exécution), le timeout et, si pertinent, les seuils d'avertissement (Warning) et critique (Critical).", en: "Set the interval (execution frequency), the timeout and, where relevant, the warning and critical thresholds." },
      { fr: "Le statut résultant (OK / Warning / Critical / Unknown) déclenche l'alerting et alimente les incidents.", en: "The resulting status (OK / Warning / Critical / Unknown) triggers alerting and feeds the incidents." },
    ],
    tips: [
      { fr: "Les seuils s'appliquent sur la valeur mesurée : par ex. temps de réponse HTTP ≥ seuil critique ⇒ Critical.", en: "Thresholds apply to the measured value: e.g. HTTP response time ≥ critical threshold ⇒ Critical." },
      { fr: "En mode SSH, laissez les identifiants vides dans le check : ils sont hérités de l'hôte.", en: "In SSH mode, leave the credentials empty in the check: they are inherited from the host." },
    ],
  },
  {
    id: "templates",
    title: { fr: "Templates de checks", en: "Check templates" },
    summary: { fr: "Modèles réutilisables pour créer des checks en série.", en: "Reusable templates to create checks in bulk." },
    body: [
      { fr: "Un template regroupe une configuration de check type (seuils, intervalle, paramètres) que vous appliquez ensuite à plusieurs hôtes d'un coup.", en: "A template bundles a standard check configuration (thresholds, interval, parameters) that you then apply to several hosts at once." },
      { fr: "Idéal pour standardiser la supervision d'une flotte homogène (parc de serveurs Windows, équipements réseau d'un même modèle…).", en: "Ideal to standardize the monitoring of a homogeneous fleet (a set of Windows servers, network devices of the same model…)." },
    ],
  },
  {
    id: "incidents",
    title: { fr: "Incidents", en: "Incidents" },
    summary: { fr: "Regroupement des alertes actives à traiter.", en: "Grouping of active alerts to handle." },
    body: [
      { fr: "Le centre d'incidents liste les problèmes en cours, triés par sévérité. Un incident naît d'un changement d'état d'un check (passage en Warning/Critical).", en: "The incident center lists ongoing problems, sorted by severity. An incident is born from a check's state change (moving to Warning/Critical)." },
      { fr: "Acquittez un incident pour signaler qu'il est pris en charge (l'escalade des notifications s'interrompt), puis résolvez-le une fois traité.", en: "Acknowledge an incident to signal it is being handled (notification escalation stops), then resolve it once addressed." },
    ],
    tips: [{ fr: "L'acquittement stoppe les rappels de notification sans masquer le problème.", en: "Acknowledgment stops notification reminders without hiding the problem." }],
  },
  {
    id: "tickets",
    title: { fr: "Tickets", en: "Tickets" },
    summary: { fr: "Suivi des interventions liées aux incidents.", en: "Tracking of interventions linked to incidents." },
    body: [
      { fr: "Un ticket formalise une intervention : titre, priorité, description, tâches et commentaires. Il peut être créé manuellement ou automatiquement à partir d'un incident.", en: "A ticket formalizes an intervention: title, priority, description, tasks and comments. It can be created manually or automatically from an incident." },
      { fr: "Assignez le ticket, suivez son avancement via les tâches, et documentez la résolution dans les commentaires.", en: "Assign the ticket, track its progress via the tasks, and document the resolution in the comments." },
    ],
    tips: [
      { fr: "Quand un ticket est résolu automatiquement, la raison est tracée dans son historique.", en: "When a ticket is auto-resolved, the reason is recorded in its history." },
      { fr: "Dans un commentaire, utilisez Maj+Entrée pour un retour à la ligne sans envoyer.", en: "In a comment, use Shift+Enter for a line break without sending." },
    ],
  },
  {
    id: "apm",
    title: { fr: "APM", en: "APM" },
    summary: { fr: "Supervision applicative : requêtes, erreurs, latence.", en: "Application monitoring: requests, errors, latency." },
    body: [
      { fr: "L'APM suit la santé des applications instrumentées : débit de requêtes, taux d'erreurs et latence moyenne.", en: "APM tracks the health of instrumented applications: request throughput, error rate and average latency." },
      { fr: "Orbisys s'auto-supervise et apparaît comme une première application ; ajoutez les vôtres via l'endpoint d'ingestion APM.", en: "Orbisys self-monitors and appears as a first application; add your own via the APM ingestion endpoint." },
    ],
  },
  {
    id: "containers",
    title: { fr: "Conteneurs", en: "Containers" },
    summary: { fr: "État des conteneurs Docker de l'hôte.", en: "State of the host's Docker containers." },
    body: [
      { fr: "Cette vue liste les conteneurs Docker et leurs métriques (CPU, mémoire, état). Le premier chargement peut prendre quelques secondes le temps d'interroger le démon Docker.", en: "This view lists the Docker containers and their metrics (CPU, memory, state). The first load may take a few seconds while querying the Docker daemon." },
    ],
  },
  {
    id: "bam",
    title: { fr: "Services métier (BAM)", en: "Business services (BAM)" },
    summary: { fr: "Vision métier agrégée à partir de composants techniques.", en: "Business view aggregated from technical components." },
    body: [
      { fr: "Un service métier (Business Activity Monitoring) agrège plusieurs checks/hôtes en un indicateur unique reflétant la disponibilité d'un service rendu (ex. « Messagerie », « Site e-commerce »).", en: "A business service (Business Activity Monitoring) aggregates several checks/hosts into a single indicator reflecting the availability of a delivered service (e.g. “Email”, “E-commerce site”)." },
      { fr: "Définissez la règle d'agrégation (au pire, pondérée…) pour obtenir un état métier lisible par les non-techniciens.", en: "Define the aggregation rule (worst-case, weighted…) to get a business state readable by non-technical people." },
    ],
  },
  {
    id: "maintenance",
    title: { fr: "Maintenances", en: "Maintenance" },
    summary: { fr: "Fenêtres planifiées qui suspendent l'alerting.", en: "Scheduled windows that suspend alerting." },
    body: [
      { fr: "Une fenêtre de maintenance met en pause les alertes d'un hôte ou d'un check sur une plage horaire donnée, pour éviter les fausses alertes pendant les opérations planifiées.", en: "A maintenance window pauses the alerts of a host or a check over a given time range, to avoid false alerts during planned operations." },
    ],
  },
  {
    id: "knowledge",
    title: { fr: "Base de connaissances", en: "Knowledge base" },
    summary: { fr: "Documents de référence pour le diagnostic (RAG).", en: "Reference documents for diagnosis (RAG)." },
    body: [
      { fr: "La base de connaissances stocke des procédures et documents. L'assistant IA s'appuie dessus (recherche augmentée / RAG) pour proposer des diagnostics contextualisés.", en: "The knowledge base stores procedures and documents. The AI assistant relies on it (retrieval-augmented generation / RAG) to propose contextualized diagnoses." },
      { fr: "Importez vos runbooks, procédures Windows/Office et autres documents pour enrichir les réponses de l'assistant.", en: "Import your runbooks, Windows/Office procedures and other documents to enrich the assistant's answers." },
    ],
  },
  {
    id: "notifications",
    title: { fr: "Canaux de notification", en: "Notification channels" },
    summary: { fr: "Où et comment Orbisys prévient en cas d'alerte.", en: "Where and how Orbisys warns when an alert fires." },
    body: [
      { fr: "Configurez les canaux de sortie (e-mail, webhook, Slack, Telegram, Teams, Discord, SMS, script) dans Settings. Chaque canal peut être limité à l'escalade ou à des plages horaires.", en: "Configure the output channels (email, webhook, Slack, Telegram, Teams, Discord, SMS, script) in Settings. Each channel can be limited to escalation or to time windows." },
      { fr: "Testez un canal après création pour valider la configuration.", en: "Test a channel after creation to validate the configuration." },
    ],
  },
  {
    id: "roles",
    title: { fr: "Rôles & droits", en: "Roles & permissions" },
    summary: { fr: "Contrôle d'accès : rôles intégrés et personnalisés.", en: "Access control: built-in and custom roles." },
    body: [
      { fr: "Trois rôles intégrés : Administrateur (tout), Opérateur (modification partout), Lecteur (lecture seule).", en: "Three built-in roles: Administrator (everything), Operator (edit everywhere), Viewer (read-only)." },
      { fr: "Vous pouvez créer des rôles personnalisés avec des droits de modification à la carte, section par section (Hôtes, Checks, Tickets, etc.). La lecture reste ouverte à tout compte connecté ; les cases cochées autorisent la création/modification/suppression dans la section.", en: "You can create custom roles with à-la-carte edit rights, section by section (Hosts, Checks, Tickets, etc.). Read access stays open to any signed-in account; ticked boxes allow create/edit/delete in the section." },
      { fr: "Gérez tout cela dans Settings → « Rôles personnalisés » puis assignez le rôle à l'utilisateur.", en: "Manage all of this in Settings → “Custom roles”, then assign the role to the user." },
    ],
  },
  {
    id: "audit",
    title: { fr: "Journal d'audit", en: "Audit log" },
    summary: { fr: "Traçabilité des actions et connexions.", en: "Traceability of actions and logins." },
    body: [
      { fr: "Le journal d'audit enregistre les écritures via l'API (créations, modifications, suppressions) et les connexions, avec l'auteur, l'horodatage et l'adresse IP.", en: "The audit log records API writes (creations, modifications, deletions) and logins, with the author, timestamp and IP address." },
    ],
  },
  {
    id: "tenants",
    title: { fr: "Multi-tenant", en: "Multi-tenant" },
    summary: { fr: "Cloisonnement par organisation (MSP).", en: "Isolation per organization (MSP)." },
    body: [
      { fr: "Le mode multi-tenant cloisonne hôtes et données par organisation cliente. Un utilisateur rattaché à un tenant ne voit que le périmètre de son tenant.", en: "Multi-tenant mode isolates hosts and data per customer organization. A user attached to a tenant only sees their tenant's scope." },
    ],
  },
  {
    id: "account",
    title: { fr: "Mon compte", en: "My account" },
    summary: { fr: "Mot de passe et paramètres personnels.", en: "Password and personal settings." },
    body: [
      { fr: "Depuis Settings → « Mon compte », changez votre mot de passe (mot de passe actuel requis).", en: "From Settings → “My account”, change your password (current password required)." },
      { fr: "En cas d'oubli, utilisez le lien « Mot de passe oublié » sur l'écran de connexion : un lien de réinitialisation à usage unique est envoyé (ou journalisé si aucun SMTP n'est configuré).", en: "If forgotten, use the “Forgot password” link on the login screen: a single-use reset link is sent (or logged if no SMTP is configured)." },
    ],
  },
];

const pick = (v: LS, lang: Lang): string => v[lang] ?? v.fr;

/** Sections de documentation dans la langue demandée. */
export function getDocSections(lang: Lang): DocSection[] {
  return SECTIONS.map((s) => ({
    id: s.id,
    title: pick(s.title, lang),
    summary: pick(s.summary, lang),
    body: s.body.map((b) => pick(b, lang)),
    tips: s.tips?.map((tp) => pick(tp, lang)),
  }));
}

/** Ids disponibles (pour valider un helpTopic). */
export const DOC_IDS: string[] = SECTIONS.map((s) => s.id);
