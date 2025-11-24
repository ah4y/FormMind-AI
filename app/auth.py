"""Very small auth helper with seeded users for demo/testing.
In a real app you'd use proper password hashing and a user table.
"""
from typing import Dict, Optional

"""Very small auth helper with seeded users for demo/testing.
In a real app you'd use proper password hashing and a user table.
"""
from typing import Dict, Optional
from .db import get_db_session
from .models import User, Tenant

def get_all_users() -> list:
    """Get all users from database for login dropdown"""
    try:
        with get_db_session() as session:
            users = session.query(User).join(Tenant).all()
            result = []
            for user in users:
                result.append({
                    'id': user.id,
                    'tenant_id': user.tenant_id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'tenant_name': user.tenant.name
                })
            return result
    except Exception as e:
        print(f"Error getting users: {e}")
        # Fallback to hardcoded users if database fails
        return [
            {"id": 1, "tenant_id": 1, "email": "owner@example.com", "name": "Alice Owner", "role": "OWNER", "tenant_name": "Acme Corp"},
            {"id": 2, "tenant_id": 1, "email": "admin@example.com", "name": "Bob Admin", "role": "ADMIN", "tenant_name": "Acme Corp"},
            {"id": 3, "tenant_id": 1, "email": "editor@example.com", "name": "Carol Editor", "role": "EDITOR", "tenant_name": "Acme Corp"},
            {"id": 4, "tenant_id": 2, "email": "owner2@example.com", "name": "David Owner", "role": "OWNER", "tenant_name": "Beta Ltd"},
            {"id": 5, "tenant_id": 2, "email": "admin2@example.com", "name": "Eve Admin", "role": "ADMIN", "tenant_name": "Beta Ltd"},
        ]

# Get users from database
SEED_USERS = get_all_users()

def find_user_by_email(email: str) -> Optional[Dict]:
    for u in SEED_USERS:
        if u["email"] == email:
            return u
    return None

def login(email: str) -> Optional[Dict]:
    """Fake login for demo: return user dict if email exists."""
    return find_user_by_email(email)

def check_auth(user_session: Optional[Dict]) -> bool:
    """Check if user is authenticated"""
    return user_session is not None and 'id' in user_session

def get_user_session():
    """Get current user session from Streamlit session state"""
    import streamlit as st
    return st.session_state.get('user', None)

def require_auth():
    """Require authentication, redirect to login if not authenticated"""
    import streamlit as st
    user = get_user_session()
    if not check_auth(user):
        st.error("Please log in to access this page")
        st.stop()
    return user
