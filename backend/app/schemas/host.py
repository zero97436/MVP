from datetime import datetime

from pydantic import BaseModel, Field, field_validator

MONITORING_MODES = {"agentless", "agent", "ssh"}


def _check_mode(v: str | None) -> str | None:
    if v is not None and v not in MONITORING_MODES:
        raise ValueError(f"monitoring_mode invalide (attendu : {', '.join(sorted(MONITORING_MODES))})")
    return v


class HostBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hostname_or_ip: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    environment: str = "production"
    is_active: bool = True
    monitoring_mode: str = "agentless"
    parent_host_id: int | None = None
    tenant_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    _v_mode = field_validator("monitoring_mode")(_check_mode)


class HostCreate(HostBase):
    # Paramètres SSH (mode ssh) : {port, user, password}. Le mot de passe est chiffré au repos.
    ssh_config: dict | None = None


class HostUpdate(BaseModel):
    name: str | None = None
    hostname_or_ip: str | None = None
    description: str | None = None
    environment: str | None = None
    is_active: bool | None = None
    monitoring_mode: str | None = None
    ssh_config: dict | None = None
    parent_host_id: int | None = None
    tenant_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    _v_mode = field_validator("monitoring_mode")(_check_mode)


class HostOut(HostBase):
    id: int
    ssh_config: dict | None = None  # secrets masqués côté route
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
