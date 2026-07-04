from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_admin)]
)


def _sync_is_admin(data: dict) -> None:
    if "role" in data and data["role"] is not None:
        role = data["role"].value if hasattr(data["role"], "value") else data["role"]
        data["role"] = role
        data["is_admin"] = role == UserRole.ADMIN.value


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return UserRepository(db).list()


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_email(payload.email):
        raise HTTPException(400, "Email déjà utilisé")
    data = payload.model_dump()
    pwd = data.pop("password")
    _sync_is_admin(data)
    return repo.create(hashed_password=hash_password(pwd), is_active=True, **data)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("password"):
        user.hashed_password = hash_password(data.pop("password"))
    else:
        data.pop("password", None)
    _sync_is_admin(data)
    return repo.update(user, **data)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current.id:
        raise HTTPException(400, "Impossible de supprimer son propre compte")
    repo.delete(user)
