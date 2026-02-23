from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.config import get_settings

_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _build_sqlalchemy_url() -> str:
    settings = get_settings()
    # POSTGRES_URL is expected to be like: postgresql://localhost:5000/myapp
    # We need SQLAlchemy URL with credentials; keep host/db from POSTGRES_URL.
    base = settings.postgres_url.replace("postgresql://", "")
    return f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}@{base}"


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine configured from env vars."""
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        _ENGINE = create_engine(_build_sqlalchemy_url(), pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)
    return _ENGINE


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    db: Session = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
