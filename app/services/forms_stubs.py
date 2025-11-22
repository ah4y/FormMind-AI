from typing import Dict, Any


_FORMS: Dict[int, Dict[str, Any]] = {}
_TEMPLATES: Dict[int, Dict[str, Any]] = {}
_NEXT_FORM_ID = 1000
_NEXT_TEMPLATE_ID = 1
_NEXT_QID = 1


def _next_form_id() -> int:
    global _NEXT_FORM_ID
    _NEXT_FORM_ID += 1
    return _NEXT_FORM_ID


def _next_template_id() -> int:
    global _NEXT_TEMPLATE_ID
    _NEXT_TEMPLATE_ID += 1
    return _NEXT_TEMPLATE_ID


def _next_qid() -> str:
    global _NEXT_QID
    _NEXT_QID += 1
    return f"q{_NEXT_QID}"


def create_form(form_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    form_id = _next_form_id()
    form = {
        "id": form_id,
        "title": form_data.get("title", "Untitled"),
        "description": form_data.get("description", ""),
        "status": form_data.get("status", "draft"),
        "created_by": user_id,
        "version": 1,
        "questions": list(form_data.get("questions", [])),
    }
    _FORMS[form_id] = form
    return form


def get_form(form_id: int) -> Dict[str, Any] | None:
    return _FORMS.get(form_id)


def list_forms() -> list[Dict[str, Any]]:
    return list(_FORMS.values())


def update_form(form_id: int, changes: Dict[str, Any], user_id: int, submissions_count: int = 0) -> Dict[str, Any]:
    existing = _FORMS.get(form_id)
    if not existing:
        raise KeyError("form not found")

    # If published and submissions exist, create a new version
    if existing.get("status") == "published" and submissions_count > 0:
        new_id = _next_form_id()
        new_form = {k: (v.copy() if isinstance(v, list) else v) for k, v in existing.items()}
        new_form["id"] = new_id
        new_form["version"] = existing.get("version", 1) + 1
        new_form.update(changes)
        _FORMS[new_id] = new_form
        return new_form

    existing.update(changes)
    _FORMS[form_id] = existing
    return existing


def add_question(form_id: int, question: Dict[str, Any]) -> Dict[str, Any]:
    form = _FORMS.get(form_id)
    if not form:
        raise KeyError("form not found")
    qid = question.get("id") or _next_qid()
    # normalize keys: support 'text' and 'label'
    q = {**question, "id": qid}
    if "label" in q and "text" not in q:
        q["text"] = q.pop("label")
    # ensure options are in normalized format (list of dicts)
    opts = q.get("options")
    if opts and all(isinstance(o, str) for o in opts):
        q["options"] = [{"label": o, "value": o} for o in opts]
    form.setdefault("questions", []).append(q)
    return q


def remove_question(form_id: int, question_id: str) -> bool:
    form = _FORMS.get(form_id)
    if not form:
        raise KeyError("form not found")
    qs = form.setdefault("questions", [])
    new_qs = [q for q in qs if q.get("id") != question_id]
    changed = len(new_qs) != len(qs)
    form["questions"] = new_qs
    return changed


def reorder_questions(form_id: int, ordered_ids: list[str]) -> None:
    form = _FORMS.get(form_id)
    if not form:
        raise KeyError("form not found")
    id_map = {q["id"]: q for q in form.get("questions", [])}
    new_qs = [id_map[i] for i in ordered_ids if i in id_map]
    form["questions"] = new_qs


def save_template(form_id: int, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    form = _FORMS.get(form_id)
    if not form:
        raise KeyError("form not found")
    tid = _next_template_id()
    tpl = {"id": tid, "form": {**form}, "meta": meta or {}}
    _TEMPLATES[tid] = tpl
    return tpl


def create_from_template(template_id: int, user_id: int) -> Dict[str, Any]:
    tpl = _TEMPLATES.get(template_id)
    if not tpl:
        raise KeyError("template not found")
    form_copy = {k: (v.copy() if isinstance(v, list) else v) for k, v in tpl["form"].items()}
    form_copy.pop("id", None)
    form_copy["status"] = "draft"
    return create_form(form_copy, user_id)
