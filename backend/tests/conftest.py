import os

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.storage.models import Base


@pytest.fixture(scope='session')
def engine():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='function')
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
        session.commit()
    finally:
        session.rollback()
        session.close()
