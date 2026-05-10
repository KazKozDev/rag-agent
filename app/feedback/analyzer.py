from collections import Counter

from app.feedback.collector import FeedbackCollector
from app.retrieval.bm25_index import tokenize


def top_failing_terms(limit: int = 20) -> list[tuple[str, int]]:
    rows = FeedbackCollector().get_low_rated(limit=200)
    counter: Counter[str] = Counter()
    for row in rows:
        query = row[1] if len(row) > 1 else ""
        counter.update(t for t in tokenize(query) if len(t) > 3)
    return counter.most_common(limit)
