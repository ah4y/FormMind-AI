"""Very small auth helper with seeded users for demo/testing.
In a real app you'd use proper password hashing and a user table.
"""
from typing import Dict, Optional

# Seeded users for demo. In real life read from DB.
SEED_USERS = [
    {"id": 1, "tenant_id": 1, "email": "owner@example.com", "name": "Owner", "role": "OWNER"},
    {"id": 2, "tenant_id": 1, "email": "editor@example.com", "name": "Editor", "role": "EDITOR"},
    {"id": 3, "tenant_id": 1, "email": "admin@example.com", "name": "Admin", "role": "ADMIN"},
]


def find_user_by_email(email: str) -> Optional[Dict]:
    for u in SEED_USERS:
        if u["email"] == email:
            return u
    return None


def login(email: str) -> Optional[Dict]:
    """Fake login for demo: return user dict if email exists."""
    return find_user_by_email(email)
