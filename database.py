"""Database connection and session setup."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set — copy .env.example to .env and fill it in.")

engine = create_engine(DATABASE_URL)

# expire_on_commit=False keeps objects readable after commit, so an endpoint can
# return the row it just wrote without triggering another query.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency yielding one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
