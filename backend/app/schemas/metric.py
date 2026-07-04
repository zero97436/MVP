from datetime import datetime

from pydantic import BaseModel, Field


class MetricIngest(BaseModel):
    """Payload poussé par un agent de collecte."""

    host_id: int | None = None
    # Alternative à host_id : résolution par hostname/IP (pratique côté agent).
    hostname_or_ip: str | None = None
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    mem_percent: float | None = Field(default=None, ge=0, le=100)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    disks: dict[str, float] | None = None
    net_mbps: float | None = Field(default=None, ge=0)
    process_count: int | None = Field(default=None, ge=0)
    load1: float | None = Field(default=None, ge=0)
    temperature: float | None = None
    collected_at: datetime | None = None


class MetricOut(BaseModel):
    id: int
    host_id: int
    cpu_percent: float | None = None
    mem_percent: float | None = None
    disk_percent: float | None = None
    disks: dict[str, float] | None = None
    net_mbps: float | None = None
    process_count: int | None = None
    load1: float | None = None
    temperature: float | None = None
    collected_at: datetime

    class Config:
        from_attributes = True


class MetricHourlyOut(BaseModel):
    host_id: int
    bucket: datetime
    cpu_avg: float | None = None
    cpu_max: float | None = None
    mem_avg: float | None = None
    mem_max: float | None = None
    disk_avg: float | None = None
    disk_max: float | None = None
    net_avg: float | None = None
    net_max: float | None = None
    sample_count: int = 0

    class Config:
        from_attributes = True


class MetricLatest(BaseModel):
    """Dernier échantillon connu pour un hôte (None si jamais collecté)."""

    host_id: int
    cpu_percent: float | None = None
    mem_percent: float | None = None
    disk_percent: float | None = None
    disks: dict[str, float] | None = None
    net_mbps: float | None = None
    process_count: int | None = None
    load1: float | None = None
    temperature: float | None = None
    collected_at: datetime | None = None
