"""Énumérations partagées."""
import enum


class CheckStatus(str, enum.Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class CheckType(str, enum.Enum):
    PING = "ping"
    TCP_PORT = "tcp_port"
    HTTP = "http"
    DISK_USAGE = "disk_usage"
    CPU_LOAD = "cpu_load"
    SSL_EXPIRY = "ssl_expiry"
    METRIC = "metric"
    SNMP = "snmp"
    DNS = "dns"
    SSH = "ssh"
    SMTP = "smtp"
    FTP = "ftp"
    DATABASE = "database"
    SSH_COMMAND = "ssh_command"
    IMAP = "imap"
    POP3 = "pop3"
    LDAP = "ldap"
    SNMP_TRAFFIC = "snmp_traffic"
    WINDOWS_SERVICE = "windows_service"
    APM = "apm"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    PROXMOX = "proxmox"
    VMWARE = "vmware"
    IPMI = "ipmi"
    NTP = "ntp"


class ChannelType(str, enum.Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TELEGRAM = "telegram"
    TEAMS = "teams"
    DISCORD = "discord"
    SMS = "sms"
    SCRIPT = "script"


class UserRole(str, enum.Enum):
    ADMIN = "admin"          # tout : gestion utilisateurs, settings, CRUD
    OPERATOR = "operator"    # CRUD hôtes/checks, run, acquittement
    VIEWER = "viewer"        # lecture seule

