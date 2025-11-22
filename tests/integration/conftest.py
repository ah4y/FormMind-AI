import os
import importlib
import pytest


# Integration tests expect a PostgreSQL instance reachable via TEST_DATABASE_URL
# If not provided, fallback to the repository default (see TODO_TEAM.md)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://formmind_user:formmind_pass@localhost:5432/formmind_db",
)


@pytest.fixture(scope="session")
def pg_engine_and_session():
    """Prepare the DB engine for integration tests and create/drop schema.

    This fixture sets `DATABASE_URL` for `app.db`, reloads the module so the
    test engine is created with the test URL, runs `init_db()` to create tables,
    and drops all tables at teardown.
    """
    # Ensure app.db picks up the test DB URL
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    # Import app.db after setting env var so engine uses TEST_DATABASE_URL
    import app.db as app_db
    importlib.reload(app_db)

    # Create tables
    created = app_db.init_db()
    if not created:
        pytest.skip("Could not initialize DB for integration tests; check TEST_DATABASE_URL")

    yield app_db.engine, app_db.get_db_session

    # Teardown: drop all tables to clean up test DB
    try:
        app_db.Base.metadata.drop_all(bind=app_db.engine)
    except Exception:
        pass
