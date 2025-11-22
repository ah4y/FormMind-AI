"""Analytics helpers: summary metrics and per-question stats.
These functions are small, pure, and unit-testable.
"""
from collections import Counter
from typing import List, Dict, Any


def summary_metrics(forms: Dict[str, Any], submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute simple summary metrics for a single form.
    - total submissions
    - unique logged-in users
    - guest submissions (guest_token present)
    - is_open (based on form submission window)
    """
    total = len(submissions)
    users = set(s["user_id"] for s in submissions if s.get("user_id"))
    guest = sum(1 for s in submissions if s.get("guest_token"))
    # form times may be None — treat as open
    now = None
    is_open = True
    ss = forms.get("submission_start")
    se = forms.get("submission_end")
    if ss and se:
        is_open = ss <= se
    return {
        "total_submissions": total,
        "unique_users": len(users),
        "guest_submissions": guest,
        "is_open": is_open,
    }


def choice_stats(question: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count selections for a choice-style question. Answers are expected as raw values.
    For checkbox (multiple) answers, values may be stored as comma-separated strings.
    """
    counter = Counter()
    for a in answers:
        v = a.get("value")
        if v is None:
            continue
        if isinstance(v, str) and "," in v:
            parts = [p.strip() for p in v.split(",") if p.strip()]
            counter.update(parts)
        else:
            counter.update([v])
    return dict(counter)


def numeric_stats(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    nums = []
    for a in answers:
        v = a.get("value")
        try:
            n = float(v)
            nums.append(n)
        except Exception:
            continue
    if not nums:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {"count": len(nums), "min": min(nums), "max": max(nums), "avg": sum(nums) / len(nums)}


def text_table(answers: List[Dict[str, Any]], limit: int = 10) -> List[str]:
    # return most recent text answers (value field)
    vals = [a.get("value", "") for a in answers if a.get("value")]
    return vals[-limit:]
