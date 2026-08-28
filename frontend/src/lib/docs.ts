/** Contenu de la documentation intégrée, structuré par section.
 *  Chaque entrée est ancrée sur `id` (ex. /docs#hosts) et référencée depuis
 *  l'en-tête de la page correspondante via <PageHeader helpTopic="hosts" />. */
export interface DocSection {
  id: string;
  title: string;
  summary: string;
  body: string[];
  tips?: string[];
}

export const DOC_SECTIONS: DocSection[] = [
  {
    id: "dashboard",
    title: "Dashboard",
    summary: "Vue d'ensemble temps réel de l'état du parc.",
    body: [
      "Le Dashboard agrège l'état de tous les hôtes et checks : compteurs UP/DOWN, OK/Warning/Critical, incidents en cours et tendances récentes.",
      "Chaque indicateur (KPI) est cliquable et renvoie vers la liste filtrée correspondante : cliquez sur « Critical » pour ouvrir les incidents critiques, sur « DOWN » pour les hôtes injoignables, etc.",
    ],
    tips: [
      "Un résumé rédigé par l'IA peut synthétiser la situation si l'intégration Ollama est active.",
    ],
  },
  {
    id: "hosts",
    title: "Hôtes",
    summary: "Équipements et serveurs supervisés, et leur mode de supervision.",
    body: [
      "Un hôte représente une machine ou un équipement (serveur, switch, routeur, sonde…). Créez-le avec son nom, son IP/hostname et son environnement.",
      "Le champ « Mode de supervision » détermine comment Opsora collecte l'état de l'hôte :",
      "• Agentless — le serveur sonde directement l'hôte sur le réseau (ICMP, SNMP, HTTP, TCP…). C'est le mode par défaut, sans rien à installer.",
      "• Agent (push HTTPS) — un agent léger installé sur l'hôte pousse ses métriques et résultats vers Opsora. Après création, la fiche de l'hôte affiche la commande d'installation prête à copier.",
      "• SSH (tunnel) — le serveur se connecte en SSH pour exécuter les checks. Renseignez le port, l'utilisateur et le mot de passe : les checks de l'hôte réutilisent automatiquement ces identifiants.",
      "La dépendance « hôte parent » permet de supprimer les fausses alertes : si un switch amont tombe, les hôtes situés derrière sont marqués injoignables plutôt qu'en panne.",
    ],
    tips: [
      "Le mot de passe SSH est chiffré au repos et n'est jamais réaffiché en clair.",
      "La commande d'installation de l'agent (mode agent) est réservée aux administrateurs car elle contient la clé d'ingestion.",
    ],
  },
  {
    id: "checks",
    title: "Checks",
    summary: "Tests unitaires exécutés périodiquement sur un hôte.",
    body: [
      "Un check est une vérification récurrente (ping, port TCP, HTTP, SNMP, espace disque, service Windows, requête SQL…). Choisissez le type : le formulaire affiche alors une aide contextuelle et pré-remplit un exemple de configuration.",
      "Réglez l'intervalle (fréquence d'exécution), le timeout et, si pertinent, les seuils d'avertissement (Warning) et critique (Critical).",
      "Le statut résultant (OK / Warning / Critical / Unknown) déclenche l'alerting et alimente les incidents.",
    ],
    tips: [
      "Les seuils s'appliquent sur la valeur mesurée : par ex. temps de réponse HTTP ≥ seuil critique ⇒ Critical.",
      "En mode SSH, laissez les identifiants vides dans le check : ils sont hérités de l'hôte.",
    ],
  },
  {
    id: "templates",
    title: "Templates de checks",
    summary: "Modèles réutilisables pour créer des checks en série.",
    body: [
      "Un template regroupe une configuration de check type (seuils, intervalle, paramètres) que vous appliquez ensuite à plusieurs hôtes d'un coup.",
      "Idéal pour standardiser la supervision d'une flotte homogène (parc de serveurs Windows, équipements réseau d'un même modèle…).",
    ],
  },
  {
    id: "incidents",
    title: "Incidents",
    summary: "Regroupement des alertes actives à traiter.",
    body: [
      "Le centre d'incidents liste les problèmes en cours, triés par sévérité. Un incident naît d'un changement d'état d'un check (passage en Warning/Critical).",
      "Acquittez un incident pour signaler qu'il est pris en charge (l'escalade des notifications s'interrompt), puis résolvez-le une fois traité.",
    ],
    tips: ["L'acquittement stoppe les rappels de notification sans masquer le problème."],
  },
  {
    id: "tickets",
    title: "Tickets",
    summary: "Suivi des interventions liées aux incidents.",
    body: [
      "Un ticket formalise une intervention : titre, priorité, description, tâches et commentaires. Il peut être créé manuellement ou automatiquement à partir d'un incident.",
      "Assignez le ticket, suivez son avancement via les tâches, et documentez la résolution dans les commentaires.",
    ],
    tips: [
      "Quand un ticket est résolu automatiquement, la raison est tracée dans son historique.",
      "Dans un commentaire, utilisez Maj+Entrée pour un retour à la ligne sans envoyer.",
    ],
  },
  {
    id: "apm",
    title: "APM",
    summary: "Supervision applicative : requêtes, erreurs, latence.",
    body: [
      "L'APM suit la santé des applications instrumentées : débit de requêtes, taux d'erreurs et latence moyenne.",
      "Opsora s'auto-supervise et apparaît comme une première application ; ajoutez les vôtres via l'endpoint d'ingestion APM.",
    ],
  },
  {
    id: "containers",
    title: "Conteneurs",
    summary: "État des conteneurs Docker de l'hôte.",
    body: [
      "Cette vue liste les conteneurs Docker et leurs métriques (CPU, mémoire, état). Le premier chargement peut prendre quelques secondes le temps d'interroger le démon Docker.",
    ],
  },
  {
    id: "bam",
    title: "Services métier (BAM)",
    summary: "Vision métier agrégée à partir de composants techniques.",
    body: [
      "Un service métier (Business Activity Monitoring) agrège plusieurs checks/hôtes en un indicateur unique reflétant la disponibilité d'un service rendu (ex. « Messagerie », « Site e-commerce »).",
      "Définissez la règle d'agrégation (au pire, pondérée…) pour obtenir un état métier lisible par les non-techniciens.",
    ],
  },
  {
    id: "maintenance",
    title: "Maintenances",
    summary: "Fenêtres planifiées qui suspendent l'alerting.",
    body: [
      "Une fenêtre de maintenance met en pause les alertes d'un hôte ou d'un check sur une plage horaire donnée, pour éviter les fausses alertes pendant les opérations planifiées.",
    ],
  },
  {
    id: "knowledge",
    title: "Base de connaissances",
    summary: "Documents de référence pour le diagnostic (RAG).",
    body: [
      "La base de connaissances stocke des procédures et documents. L'assistant IA s'appuie dessus (recherche augmentée / RAG) pour proposer des diagnostics contextualisés.",
      "Importez vos runbooks, procédures Windows/Office et autres documents pour enrichir les réponses de l'assistant.",
    ],
  },
  {
    id: "notifications",
    title: "Canaux de notification",
    summary: "Où et comment Opsora prévient en cas d'alerte.",
    body: [
      "Configurez les canaux de sortie (e-mail, webhook, Slack, Telegram, Teams, Discord, SMS, script) dans Settings. Chaque canal peut être limité à l'escalade ou à des plages horaires.",
      "Testez un canal après création pour valider la configuration.",
    ],
  },
  {
    id: "roles",
    title: "Rôles & droits",
    summary: "Contrôle d'accès : rôles intégrés et personnalisés.",
    body: [
      "Trois rôles intégrés : Administrateur (tout), Opérateur (modification partout), Lecteur (lecture seule).",
      "Vous pouvez créer des rôles personnalisés avec des droits de modification à la carte, section par section (Hôtes, Checks, Tickets, etc.). La lecture reste ouverte à tout compte connecté ; les cases cochées autorisent la création/modification/suppression dans la section.",
      "Gérez tout cela dans Settings → « Rôles personnalisés » puis assignez le rôle à l'utilisateur.",
    ],
  },
  {
    id: "audit",
    title: "Journal d'audit",
    summary: "Traçabilité des actions et connexions.",
    body: [
      "Le journal d'audit enregistre les écritures via l'API (créations, modifications, suppressions) et les connexions, avec l'auteur, l'horodatage et l'adresse IP.",
    ],
  },
  {
    id: "tenants",
    title: "Multi-tenant",
    summary: "Cloisonnement par organisation (MSP).",
    body: [
      "Le mode multi-tenant cloisonne hôtes et données par organisation cliente. Un utilisateur rattaché à un tenant ne voit que le périmètre de son tenant.",
    ],
  },
  {
    id: "account",
    title: "Mon compte",
    summary: "Mot de passe et paramètres personnels.",
    body: [
      "Depuis Settings → « Mon compte », changez votre mot de passe (mot de passe actuel requis).",
      "En cas d'oubli, utilisez le lien « Mot de passe oublié » sur l'écran de connexion : un lien de réinitialisation à usage unique est envoyé (ou journalisé si aucun SMTP n'est configuré).",
    ],
  },
];

/** Accès direct par id (pour valider un helpTopic). */
export const DOC_BY_ID: Record<string, DocSection> = Object.fromEntries(
  DOC_SECTIONS.map((s) => [s.id, s]),
);
