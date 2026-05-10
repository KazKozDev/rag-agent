from app.feedback.collector import FeedbackCollector


def test_record_and_retrieve():
    c = FeedbackCollector()
    fid = c.record(
        query="What is the termination policy?",
        answer="30 days notice.",
        sources=["[Source: contract.pdf, p. 12]"],
        rating=-1,
        comment="incomplete",
    )
    assert fid

    low = c.get_low_rated(limit=10)
    assert len(low) == 1

    stats = c.get_stats()
    assert stats == {"total": 1, "upvotes": 0, "downvotes": 1}


def test_feedback_stats_empty():
    stats = FeedbackCollector().get_stats()
    assert stats == {"total": 0, "upvotes": 0, "downvotes": 0}


def test_feedback_multiple_records():
    c = FeedbackCollector()
    c.record("q1", "a1", [], 1)
    c.record("q2", "a2", [], 1)
    c.record("q3", "a3", [], -1)
    c.record("q4", "a4", [], -1)
    c.record("q5", "a5", [], -1)

    stats = c.get_stats()
    assert stats == {"total": 5, "upvotes": 2, "downvotes": 3}
    assert len(c.get_low_rated(limit=2)) == 2
