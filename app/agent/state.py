from typing import TypedDict, List, Optional, Literal, Dict, Any


class AgentState(TypedDict, total=False):
    query: str
    original_query: str
    route: Literal["rag", "faq", "escalate", "clarify"]
    needs_clarification: bool
    clarification_question: Optional[str]
    retrieved_nodes: List[dict]
    answer: str
    citations: List[str]
    validated: bool
    error: Optional[str]
    # retry loop
    attempts: int
    # self-query filters extracted from the user query
    metadata_filters: Optional[Dict[str, Any]]
    # session continuation (created on clarify, consumed on next request)
    session_id: Optional[str]
