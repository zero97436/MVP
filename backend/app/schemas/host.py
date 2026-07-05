from datetime import datetime

from pydantic import BaseModel, Field


class HostBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hostname_or_ip: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    environment: str = "production"
    is_active: bool = True
    parent_host_id: int | None = None
    tenant_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class HostCreate(HostBase):
    pass


class HostUpdate(BaseModel):
    name: str | None = None
    hostname_or_ip: str | None = None
    description: str | None = None
    environment: str | None = None
    is_active: bool | None = None
    parent_host_id: int | None = None
    tenant_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class HostOut(HostBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
