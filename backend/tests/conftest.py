"""Fixtures de test : base SQLite en mémoire + client FastAPI authentifié."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
# IA injoignable en test -> l'endpoint d'analyse répond 503 immédiatement (pas d'appel réel).
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:9")
# Tests indépendants du déploiement : ingestion ouverte (override l'éventuelle clé du conteneur).
os.environ["INGEST_API_KEY"] = ""
os.environ["ITSM_AUTO_CREATE"] = "false"  # isolé : testé explicitement via monkeypatch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db import session as session_module
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User

# Moteur SQLite partagé en mémoire pour toute la session de test.
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _override_get_db():
    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    session_module.SessionLocal = TestingSessionLocal
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _full_license(monkeypatch):
    """Par défaut, les tests tournent en licence Enterprise (toutes features).

    Les tests du gating de licence rétablissent Community explicitement."""
    import app.core.license as lic

    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "enterprise", "max_hosts": None,
        "features": sorted(lic.ALL_FEATURES), "customer": "tests", "expires": None,
    })
    yield


@pytest.fixture
def admin(db):
    user = db.query(User).filter_by(email="admin@local").first()
    if not user:
        user = User(
            email="admin@local",
            hashed_password=hash_password("admin1234"),
            is_admin=True,
            is_active=True,
            role="admin",
        )
        db.add(user)
        db.commit()
    return user


@pytest.fixture
def client(admin):
    c = TestClient(app)
    resp = c.post("/api/auth/login", json={"email": "admin@local", "password": "admin1234"})
    token = resp.json()["access_token"]
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c
