from app.feedback.analyzer import top_failing_terms
from app.feedback.collector import FeedbackCollector


def weekly_report() -> str:
    stats = FeedbackCollector().get_stats()
    failing = top_failing_terms()
    lines = [
        "# Weekly Feedback Report",
        f"- Total feedback: {stats['total']}",
        f"- Upvotes: {stats['upvotes']}",
        f"- Downvotes: {stats['downvotes']}",
        "",
        "## Top failing terms",
    ]
    if failing:
        lines.extend(f"- {term}: {count}" for term, count in failing)
    else:
        lines.append("- (none)")
    return "\n".join(lines)
