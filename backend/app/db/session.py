"""Session SQLAlchemy."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session et la ferme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
