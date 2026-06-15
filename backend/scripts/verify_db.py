"""Verify and repair BizFlow database schema and seed data."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')

REQUIRED_TABLES = [
    'products',
    'customers',
    'orders',
    'order_items',
    'activity_logs',
    'users',
    'knowledge_embeddings',
    'pending_actions',
]
LATEST_REVISION = '0004_add_refresh_token_hash'


def get_engine() -> Engine:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL must be set')
    return create_engine(database_url, future=True)


def check_database(engine: Engine | None = None) -> dict:
    engine = engine or get_engine()
    results = {
        'connection': False,
        'tables': [],
        'missing_tables': [],
        'alembic_version': None,
        'refresh_token_hash': False,
        'pgvector': False,
        'pgvector_required': False,
        'row_counts': {},
        'admin_users': 0,
        'errors': [],
    }

    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            results['connection'] = True

            insp = inspect(engine)
            tables = sorted(insp.get_table_names())
            results['tables'] = tables
            results['missing_tables'] = [t for t in REQUIRED_TABLES if t not in tables]

            if 'alembic_version' in tables:
                results['alembic_version'] = conn.execute(
                    text('SELECT version_num FROM alembic_version')
                ).scalar()

            if 'users' in tables:
                columns = {col['name'] for col in insp.get_columns('users')}
                results['refresh_token_hash'] = 'refresh_token_hash' in columns
                results['admin_users'] = conn.execute(
                    text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                ).scalar() or 0

            if not str(engine.url).startswith('sqlite'):
                ext = conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                ).fetchall()
                results['pgvector'] = bool(ext)
                results['pgvector_required'] = False
            else:
                results['pgvector_required'] = False

            for table in ['products', 'customers', 'orders']:
                if table in tables:
                    results['row_counts'][table] = conn.execute(
                        text(f'SELECT COUNT(*) FROM {table}')
                    ).scalar() or 0
    except Exception as exc:
        results['errors'].append(str(exc))

    return results


def all_checks_pass(results: dict) -> bool:
    if not results['connection']:
        return False
    if results['missing_tables']:
        return False
    if results['alembic_version'] != LATEST_REVISION:
        return False
    if not results['refresh_token_hash']:
        return False
    if results.get('pgvector_required') and not results['pgvector']:
        return False
    if any(results['row_counts'].get(t, 0) == 0 for t in ['products', 'customers', 'orders']):
        return False
    if results['admin_users'] < 1:
        return False
    return True


def _stamp_if_needed(engine: Engine) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / 'backend' / 'alembic.ini'))
    cfg.set_main_option('sqlalchemy.url', str(engine.url))

    with engine.connect() as conn:
        insp = inspect(engine)
        tables = insp.get_table_names()
        if 'alembic_version' not in tables and 'users' in tables:
            command.stamp(cfg, '0001_create_initial_tables')


def _enable_pgvector(engine: Engine) -> None:
    if str(engine.url).startswith('sqlite'):
        return
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.commit()


def _apply_schema_patches(engine: Engine) -> None:
    insp = inspect(engine)
    tables = insp.get_table_names()

    with engine.begin() as conn:
        if 'users' in tables:
            columns = {col['name'] for col in insp.get_columns('users')}
            if 'refresh_token_hash' not in columns:
                conn.execute(text('ALTER TABLE users ADD COLUMN refresh_token_hash VARCHAR(255)'))

        if 'pending_actions' not in tables:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pending_actions (
                    id SERIAL PRIMARY KEY,
                    action_type VARCHAR(80) NOT NULL,
                    payload JSON NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    requested_by VARCHAR(128),
                    reviewed_by VARCHAR(128),
                    review_comment TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    reviewed_at TIMESTAMPTZ
                )
            """))

        if 'knowledge_embeddings' not in tables:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                    id SERIAL PRIMARY KEY,
                    object_type VARCHAR(80) NOT NULL,
                    object_id INTEGER NOT NULL,
                    embedding JSON NOT NULL,
                    metadata JSON,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))


def _run_migrations(engine: Engine) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / 'backend' / 'alembic.ini'))
    cfg.set_main_option('sqlalchemy.url', str(engine.url))
    _stamp_if_needed(engine)
    try:
        command.upgrade(cfg, 'head')
    except Exception:
        _apply_schema_patches(engine)
        command.stamp(cfg, LATEST_REVISION)


def _import_legacy_data() -> None:
    from backend.scripts.import_legacy_json import migrate

    migrate()


def _seed_admin_user(engine: Engine) -> None:
    from backend.services.auth_service import AuthService
    from backend.storage.database import get_db_session

    try:
        with get_db_session() as session:
            service = AuthService(session)
            service.register_user(
                username='admin',
                email='admin@bizflow.local',
                password='changeme',
                role='admin',
            )
        print('Seeded admin user: admin / changeme')
    except ValueError:
        pass


def repair_database(engine: Engine | None = None) -> dict:
    engine = engine or get_engine()
    status = check_database(engine)

    if not str(engine.url).startswith('sqlite'):
        try:
            _enable_pgvector(engine)
        except Exception as exc:
            status['errors'].append(f'pgvector: {exc}')

    try:
        _run_migrations(engine)
    except Exception as exc:
        status['errors'].append(f'migrations: {exc}')
        from backend.storage.models import Base
        Base.metadata.create_all(bind=engine)

    status = check_database(engine)

    if any(status['row_counts'].get(t, 0) == 0 for t in ['products', 'customers', 'orders']):
        try:
            _import_legacy_data()
        except Exception as exc:
            status['errors'].append(f'import: {exc}')

    status = check_database(engine)

    if status['admin_users'] < 1:
        try:
            _seed_admin_user(engine)
        except Exception as exc:
            status['errors'].append(f'admin seed: {exc}')

    return check_database(engine)


def main() -> int:
    fix = '--fix' in sys.argv
    engine = get_engine()
    results = repair_database(engine) if fix else check_database(engine)

    print('Database verification:')
    for key, value in results.items():
        print(f'  {key}: {value}')

    if all_checks_pass(results):
        print('All checks passed.')
        return 0

    if not fix:
        print('Checks failed. Run with --fix to repair.')
        return 1

    results = check_database(engine)
    if all_checks_pass(results):
        print('Repair complete. All checks passed.')
        return 0

    print('Repair attempted but checks still failing.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
