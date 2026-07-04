from pydantic import BaseModel


class LoginRequest(BaseModel):
    # str (et non EmailStr) pour autoriser l'identifiant de démo `admin@local`.
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_admin: bool
    role: str = "viewer"

    class Config:
        from_attributes = True
