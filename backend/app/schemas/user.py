from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str | None = None
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    role: str
    is_admin: bool
    is_active: bool
    tenant_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
