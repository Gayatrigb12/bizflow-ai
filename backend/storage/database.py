import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL must be set in .env or environment variables')
Base = declarative_base() 

# Create engine with sensible pool settings for the selected driver.
# When running tests the project uses an in-memory sqlite URL which does
# not accept PostgreSQL pool kwargs like `max_overflow` or `pool_timeout`.
is_sqlite = DATABASE_URL.startswith('sqlite')
if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def pgvector_enabled() -> bool:
    if is_sqlite:
        return False
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()
            return row is not None
    except Exception:
        return False


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_migrations() -> None:
    if is_sqlite:
        return
    try:
        from pathlib import Path
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
        cfg.set_main_option('sqlalchemy.url', DATABASE_URL)
        command.upgrade(cfg, 'head')
    except Exception:
        pass


def init_db() -> None:
    from backend.storage.models import Base

    run_migrations()
    Base.metadata.create_all(bind=engine)
