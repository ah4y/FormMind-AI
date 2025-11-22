import pytest

from app.services.forms import FormsService


def test_forms_create_and_get(pg_engine_and_session):
    engine, get_db_session = pg_engine_and_session

    # Create a tenant and a user, then create a form via FormsService
    with get_db_session() as session:
        # Insert a tenant and user directly for required foreign keys
        tenant = session.execute("INSERT INTO tenants (name) VALUES ('testt') RETURNING id").fetchone()
        tenant_id = tenant[0]
        user = session.execute(
            "INSERT INTO users (tenant_id, email, role) VALUES (:t, :e, :r) RETURNING id",
            {"t": tenant_id, "e": "test@example.com", "r": "OWNER"},
        ).fetchone()
        user_id = user[0]

    # Use FormsService to create a form
    created = FormsService.create_form(
        title="IntForm",
        description="Integration test form",
        created_by=user_id,
        tenant_id=tenant_id,
    )

    assert created is not None and "id" in created

    # Retrieve via service
    got = FormsService.get_form_by_id(created["id"], user_id=user_id, user_role="OWNER")
    assert got is not None
    assert got["title"] == "IntForm"
