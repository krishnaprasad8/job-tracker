"""Shared fixtures. Tests run against a real Postgres database, not SQLite,
because the status column is a native Postgres enum that SQLite cannot model."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import main
from app.database import get_db
from app.models import Base


def _test_database_url():
    """Same server as DATABASE_URL, but a dedicated <name>_test database."""
    url = make_url(os.environ["DATABASE_URL"])
    return url.set(database=f"{url.database}_test")


def _create_test_database_if_missing(url):
    # CREATE DATABASE cannot run inside a transaction, hence AUTOCOMMIT.
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    url = _test_database_url()
    _create_test_database_if_missing(url)
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine):
    """Empty the table after each test so tests cannot affect one another."""
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE applications RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(engine):
    """TestClient with get_db redirected at the test database."""
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
