"""Self-query analyzer: extract metadata filters from a natural-language query.

Output is a (possibly empty) dict like {"file_name": "contract.pdf",
"page_number": 4}. Filters are applied as a post-filter on retrieve results
in HybridRetriever.

Kept intentionally narrow: only file_name and page_number, because that is
all the loader writes into metadata. Adding more keys means teaching the
indexer to write them first.
"""
import json
import re

from langchain_core.messages import HumanMessage

from app.agent.llm import get_chat_llm
from app.agent.state import AgentState


_PROMPT = """Extract metadata filters from a search query for a document RAG.

Available metadata keys:
- file_name: a filename, e.g. "contract.pdf". Only set if the user names a
  specific file, not a topic.
- page_number: an integer page number. Only set if the user mentions a page
  explicitly ("on page 4", "стр. 12").

Reply with ONLY a JSON object. No prose, no code fences. Examples:

Query: "what is the termination clause"
{{}}

Query: "what is on page 4 of contract.pdf"
{{"file_name": "contract.pdf", "page_number": 4}}

Query: "что написано на странице 12"
{{"page_number": 12}}

Query: {query}
"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse(raw: str) -> dict:
    raw = raw.strip()
    m = _JSON_RE.search(raw)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict = {}
    fn = data.get("file_name")
    pn = data.get("page_number")
    if isinstance(fn, str) and fn.strip():
        out["file_name"] = fn.strip()
    if isinstance(pn, int):
        out["page_number"] = pn
    elif isinstance(pn, str) and pn.strip().isdigit():
        out["page_number"] = int(pn.strip())
    return out


def query_analyzer_node(state: AgentState) -> dict:
    query = state.get("query", "")
    # Cheap heuristic: skip the LLM call if query has no digits AND no .pdf/.docx/etc.
    # This is a conservative gate — false negatives are fine, the worst case
    # is "no filter applied", which is the current behavior anyway.
    has_digit = any(c.isdigit() for c in query)
    has_ext = bool(re.search(r"\.[a-z]{2,4}\b", query.lower()))
    if not has_digit and not has_ext:
        return {"metadata_filters": None}

    llm = get_chat_llm()
    raw = llm.invoke([HumanMessage(content=_PROMPT.format(query=query))]).content
    text = raw if isinstance(raw, str) else str(raw)
    filters = _parse(text)
    return {"metadata_filters": filters or None}
