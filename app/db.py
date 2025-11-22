"""Database helpers using SQLAlchemy.
Default connection string matches the competition prompt but can be overridden
via the `DATABASE_URL` environment variable for local testing.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://formmind_user:formmind_pass@localhost:5432/formmind_db",
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()


def init_db(engine_override=None):
    """Run a minimal initialization. If models are defined, call Base.metadata.create_all.
    This works for a simple start; for production, run explicit migrations.
    """
    from . import models  # noqa: F401

    e = engine_override or engine
    Base.metadata.create_all(bind=e)
