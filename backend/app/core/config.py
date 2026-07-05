"""Configuration centralisée via variables d'environnement (Pydantic Settings)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "Opsora"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://supervision:supervision@db:5432/supervision"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # --- Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2 h (réduit la fenêtre en cas de vol de token)
    # Origines autorisées (CORS), séparées par des virgules. "*" = tout (dev only).
    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:5173"
    # Anti-bruteforce login : N échecs max par IP sur la fenêtre (secondes).
    LOGIN_MAX_ATTEMPTS: int = 10
    LOGIN_WINDOW_SECONDS: int = 300

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- Seed admin ---
    ADMIN_EMAIL: str = "admin@local"
    ADMIN_PASSWORD: str = "admin1234"

    # --- SMTP (notifications email) ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "supervision@local"
    SMTP_TLS: bool = True

    # --- Scheduler ---
    SCHEDULER_INTERVAL_SECONDS: int = 30

    # --- Détection de flapping (check qui oscille OK <-> panne) ---
    FLAPPING_ENABLED: bool = True
    FLAPPING_WINDOW: int = 20     # nb de derniers résultats analysés
    FLAPPING_THRESHOLD: int = 7   # nb de changements d'état pour déclarer le flapping

    # --- Escalade d'alertes ---
    ESCALATION_ENABLED: bool = True
    ESCALATION_AFTER_MINUTES: int = 15  # délai avant escalade d'une alerte non acquittée

    # --- IA (Ollama) ---
    # Depuis un conteneur Docker, l'hôte est joignable via host.docker.internal.
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT_SECONDS: int = 120

    # --- SSO / OIDC (Enterprise) ---
    # Compatible Keycloak, Azure AD/Entra, Google Workspace, Okta, Authentik…
    OIDC_ISSUER: str = ""          # ex. https://keycloak.acme.fr/realms/acme
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    SSO_DEFAULT_ROLE: str = "viewer"     # rôle des comptes créés via SSO
    SSO_AUTO_CREATE_USERS: bool = True   # créer le compte au 1er login SSO

    # --- Licence ---
    # Vide = version gratuite (100 hôtes max). Clé signée = limite étendue.
    LICENSE_KEY: str = ""

    # --- Page de statut publique ---
    # Expose /api/public/status et la page /status SANS authentification
    # (uniquement le nom + l'état des services métier, aucun détail technique).
    STATUS_PAGE_ENABLED: bool = True
    STATUS_PAGE_TITLE: str = "État des services"

    # --- Docker (supervision de conteneurs) ---
    # Socket de l'API Docker Engine (monté dans le conteneur via docker-compose).
    DOCKER_SOCKET: str = "/var/run/docker.sock"

    # --- ITSM / ticketing ---
    # provider : internal | webhook | jira | servicenow
    ITSM_PROVIDER: str = "internal"
    ITSM_URL: str = ""          # base URL (Jira/ServiceNow) ou URL du webhook
    ITSM_USER: str = ""         # e-mail (Jira basic auth)
    ITSM_TOKEN: str = ""        # API token / clé
    ITSM_PROJECT: str = ""      # clé de projet Jira (ex. OPS) / table ServiceNow
    ITSM_AUTO_CREATE: bool = False  # créer un ticket auto à chaque incident CRITICAL

    # --- Ingestion de métriques (agents distants) ---
    # Clé attendue dans l'en-tête X-Ingest-Key. Vide = ingestion ouverte (dev only).
    INGEST_API_KEY: str = ""

    # --- Rétention des données (purge automatique) ---
    RETENTION_CHECK_RESULTS_DAYS: int = 30   # historique des résultats de checks
    RETENTION_HOST_METRICS_DAYS: int = 15    # échantillons de métriques agent (bruts)
    RETENTION_HOST_METRICS_HOURLY_DAYS: int = 365  # rollups horaires (long terme)
    RETENTION_RESOLVED_ALERTS_DAYS: int = 90  # alertes résolues (inactives)
    RETENTION_EVENTS_DAYS: int = 90  # journal d'événements
    RETENTION_PURGE_INTERVAL_MINUTES: int = 60  # fréquence purge + downsampling auto


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
