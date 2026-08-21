"""
Database session factory and engine configuration.
All DB access goes through the session returned by get_db().
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Declarative Base ──────────────────────────────────────
class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    All models must inherit from this class.
    """
    pass


# ── SQLAlchemy Engine ─────────────────────────────────────
db_url = settings.effective_database_url

# Fallback to SQLite local file if PostgreSQL is not reachable (e.g. running outside Docker container)
try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=(settings.environment == "development"),
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    # Auto-create all tables in PostgreSQL
    import app.models  # noqa: F401
    Base.metadata.create_all(engine)
    from app.core.db_migrations import run_migrations
    run_migrations(engine)
    logger.info("Successfully connected to PostgreSQL database at %s", db_url)
except Exception as e:
    # LOUD warning/error for local development fallback
    logger.error("=" * 80)
    logger.error("  CRITICAL DATABASE NOTICE: PostgreSQL connection failed!")
    logger.error("  Connection DSN: %s", db_url)
    logger.error("  Error Details: %s", e)
    logger.error("  FALLING BACK TO LOCAL SQLITE DATABASE (dev_logistics.db) FOR DEVELOPMENT.")
    logger.error("=" * 80)
    db_url = "sqlite:///./dev_logistics.db"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=(settings.environment == "development"),
    )
    # Auto-import all models to register with Base.metadata
    import app.models  # noqa: F401
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for table in Base.metadata.tables.values():
         for col in table.columns:
             if isinstance(col.type, JSONB):
                 col.type = JSON()
    Base.metadata.create_all(engine)
    from app.core.db_migrations import run_migrations
    run_migrations(engine)

# ── Session Factory ───────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Dependency ────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that yields a database session per request
    and guarantees cleanup even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
