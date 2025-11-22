"""Form-related business logic.
Includes versioning decision helper and simple create/edit helpers (DB-agnostic helpers).
"""
from typing import Dict, Any


def needs_new_version_on_edit(form: Dict[str, Any], submissions_count: int) -> bool:
    """Decide whether an edit should create a new form version.

    Rules:
    - If form.status == 'published' and submissions_count > 0 => new version needed
    - If submissions_count == 0 => can edit in place
    - Otherwise conservative path: create new version when published
    """
    status = form.get("status", "draft")
    if submissions_count == 0:
        return False
    if status == "published" and submissions_count > 0:
        return True
    return False


def role_can_edit(user_role: str, user_id: int, form: Dict[str, Any]) -> bool:
    """Enforce simple role rules described in the prompt.
    - OWNER and ADMIN can manage all tenant forms
    - EDITOR can only manage forms they created (created_by)
    """
    if user_role in ("OWNER", "ADMIN"):
        return True
    if user_role == "EDITOR":
        return form.get("created_by") == user_id
    return False
