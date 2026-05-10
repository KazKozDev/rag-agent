import re

_CITATION_RE = re.compile(r"\[Source:[^\]]+\]")


def format_citation(node) -> str:
    """Format citation. Accepts NodeWithScore or a raw object exposing metadata."""
    if hasattr(node, "node") and hasattr(node.node, "metadata"):
        metadata = node.node.metadata or {}
    elif hasattr(node, "metadata"):
        metadata = node.metadata or {}
    else:
        metadata = node.get("metadata", {}) if isinstance(node, dict) else {}

    filename = metadata.get("file_name", "unknown")
    page = metadata.get("page_number") or metadata.get("page_label")

    if page:
        return f"[Source: {filename}, p. {page}]"
    return f"[Source: {filename}]"


def parse_citations(answer: str) -> list[str]:
    return _CITATION_RE.findall(answer)
