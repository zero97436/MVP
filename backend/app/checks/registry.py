"""Registre des plugins de check (extensible)."""
from app.checks.base import BaseCheck
from app.checks.plugins.ping import PingCheck
from app.checks.plugins.tcp_port import TcpPortCheck
from app.checks.plugins.http import HttpCheck
from app.checks.plugins.ssl_expiry import SslExpiryCheck
from app.checks.plugins.disk_usage import DiskUsageCheck
from app.checks.plugins.cpu_load import CpuLoadCheck
from app.checks.plugins.metric_threshold import MetricThresholdCheck
from app.checks.plugins.snmp import SnmpCheck
from app.checks.plugins.dns import DnsCheck
from app.checks.plugins.ssh import SshCheck
from app.checks.plugins.smtp import SmtpCheck
from app.checks.plugins.ftp import FtpCheck
from app.checks.plugins.database import DatabaseCheck
from app.checks.plugins.ssh_command import SshCommandCheck
from app.checks.plugins.imap import ImapCheck
from app.checks.plugins.pop3 import Pop3Check
from app.checks.plugins.ldap import LdapCheck
from app.checks.plugins.snmp_traffic import SnmpTrafficCheck
from app.checks.plugins.windows_service import WindowsServiceCheck
from app.checks.plugins.apm import ApmCheck
from app.checks.plugins.docker import DockerCheck
from app.checks.plugins.kubernetes import KubernetesCheck
from app.checks.plugins.proxmox import ProxmoxCheck
from app.checks.plugins.vmware import VmwareCheck
from app.checks.plugins.ipmi import IpmiCheck
from app.checks.plugins.ntp import NtpCheck

# Mapping type -> classe. Ajouter un plugin = ajouter une ligne ici.
CHECK_REGISTRY: dict[str, type[BaseCheck]] = {
    PingCheck.type: PingCheck,
    TcpPortCheck.type: TcpPortCheck,
    HttpCheck.type: HttpCheck,
    SslExpiryCheck.type: SslExpiryCheck,
    DiskUsageCheck.type: DiskUsageCheck,
    CpuLoadCheck.type: CpuLoadCheck,
    MetricThresholdCheck.type: MetricThresholdCheck,
    SnmpCheck.type: SnmpCheck,
    DnsCheck.type: DnsCheck,
    SshCheck.type: SshCheck,
    SmtpCheck.type: SmtpCheck,
    FtpCheck.type: FtpCheck,
    DatabaseCheck.type: DatabaseCheck,
    SshCommandCheck.type: SshCommandCheck,
    ImapCheck.type: ImapCheck,
    Pop3Check.type: Pop3Check,
    LdapCheck.type: LdapCheck,
    SnmpTrafficCheck.type: SnmpTrafficCheck,
    WindowsServiceCheck.type: WindowsServiceCheck,
    ApmCheck.type: ApmCheck,
    DockerCheck.type: DockerCheck,
    KubernetesCheck.type: KubernetesCheck,
    ProxmoxCheck.type: ProxmoxCheck,
    VmwareCheck.type: VmwareCheck,
    IpmiCheck.type: IpmiCheck,
    NtpCheck.type: NtpCheck,
}


def get_check(check_type: str) -> BaseCheck | None:
    cls = CHECK_REGISTRY.get(check_type)
    return cls() if cls else None
