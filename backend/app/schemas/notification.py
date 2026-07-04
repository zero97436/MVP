from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.crypto import redact_config
from app.models.enums import ChannelType


class NotificationChannelBase(BaseModel):
    name: str = Field(..., min_length=1)
    type: ChannelType
    config_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    escalation_only: bool = False
    active_hours: str | None = None


class NotificationChannelCreate(NotificationChannelBase):
    pass


class NotificationChannelOut(NotificationChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _redact(self):
        self.config_json = redact_config(self.config_json)
        return self
