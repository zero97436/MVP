from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.crypto import redact_config
from app.models.enums import CheckType


class CheckBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: CheckType
    interval_seconds: int = Field(60, ge=5)
    timeout_seconds: int = Field(10, ge=1)
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    executor_host_id: int | None = None


class CheckCreate(CheckBase):
    host_id: int


class CheckUpdate(BaseModel):
    name: str | None = None
    type: CheckType | None = None
    interval_seconds: int | None = Field(None, ge=5)
    timeout_seconds: int | None = Field(None, ge=1)
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    config_json: dict[str, Any] | None = None
    is_active: bool | None = None
    executor_host_id: int | None = None


class CheckOut(CheckBase):
    id: int
    host_id: int
    last_status: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _redact(self):
        self.config_json = redact_config(self.config_json)
        return self
