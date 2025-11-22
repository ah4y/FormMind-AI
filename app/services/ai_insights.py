"""Simple local AI-style insights for text responses.
Provides top keywords, length stats, and a tiny sentiment heuristic.
"""
from collections import Counter
import re
from typing import List, Dict

STOPWORDS = set(
    [
        "the",
        "and",
        "a",
        "an",
        "to",
        "is",
        "in",
        "it",
        "of",
        "for",
        "on",
        "that",
        "this",
        "with",
        "as",
        "are",
        "was",
    ]
)

POSITIVE = {"good", "great", "excellent", "happy", "love", "like", "nice", "positive"}
NEGATIVE = {"bad", "poor", "hate", "terrible", "awful", "negative", "sad"}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"\b[\w']+\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


def top_keywords(responses: List[str], top_n: int = 10) -> List[Dict[str, int]]:
    counter = Counter()
    for r in responses:
        counter.update(_tokenize(r))
    common = counter.most_common(top_n)
    return [{"word": w, "count": c} for w, c in common]


def length_stats(responses: List[str]) -> Dict[str, float]:
    if not responses:
        return {"count": 0, "avg_words": 0.0, "min_words": 0, "max_words": 0}
    lens = [len(_tokenize(r)) for r in responses]
    return {
        "count": len(lens),
        "avg_words": sum(lens) / len(lens),
        "min_words": min(lens),
        "max_words": max(lens),
    }


def simple_sentiment(responses: List[str]) -> Dict[str, int]:
    """Label each response as positive/negative/neutral by simple word matching."""
    out = {"positive": 0, "neutral": 0, "negative": 0}
    for r in responses:
        toks = set(_tokenize(r))
        pos_hits = len(toks & POSITIVE)
        neg_hits = len(toks & NEGATIVE)
        if pos_hits > neg_hits:
            out["positive"] += 1
        elif neg_hits > pos_hits:
            out["negative"] += 1
        else:
            out["neutral"] += 1
    return out
