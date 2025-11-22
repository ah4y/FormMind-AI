"""Submission handling and validation helpers.
These helpers are written to be mostly DB-agnostic so tests can run in-memory.
"""
from typing import Dict, List


def can_submit(user_id, form: Dict, existing_submissions: List[Dict]) -> bool:
    """Enforce single_submission: if true, a logged-in user may only submit once."""
    if not form.get("single_submission"):
        return True
    if not user_id:
        # guests are allowed but may be tracked separately
        return True
    for s in existing_submissions:
        if s.get("user_id") == user_id and s.get("form_id") == form.get("id"):
            return False
    return True


def validate_submission(form: Dict, answers: List[Dict]) -> List[str]:
    """Simple validation for required fields. Answers is a list of {question_id, value}.
    Return list of error messages (empty if ok).
    """
    errors = []
    # For this lightweight implementation, question metadata may be embedded in form['questions']
    questions = {q['id']: q for q in form.get('questions', [])}
    for qid, q in questions.items():
        if q.get('required'):
            found = False
            for a in answers:
                if a.get('question_id') == qid and a.get('value') not in (None, ""):
                    found = True
            if not found:
                errors.append(f"Question '{q.get('label')}' is required.")
    return errors
