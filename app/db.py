"""
Database connection and session management for FormMind-AI
Uses SQLAlchemy with PostgreSQL backend
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://formmind_user:formmind_pass@localhost:5432/formmind_db",
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for all models
Base = declarative_base()


def get_session():
    """Get a new database session"""
    return SessionLocal()


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Database connection successful")
                return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    return False


def init_db(engine_override=None):
    """
    Initialize database by creating all tables
    For development only - use migrations for production
    """
    try:
        # Import models to register them with Base
        from . import models  # noqa: F401
        
        target_engine = engine_override or engine
        Base.metadata.create_all(bind=target_engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        return False
