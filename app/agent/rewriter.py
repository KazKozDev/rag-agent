"""Query rewriter for the validator-failed retry loop.

When the validator says INVALID, the typical cause is that retrieve pulled
chunks that don't actually contain the answer, and the LLM either filled the
gap with confabulation or said it didn't know. Rewriting the original query
based on what *was* retrieved often surfaces a better query for the next pass.
"""
from langchain_core.messages import HumanMessage

from app.agent.llm import get_chat_llm
from app.agent.state import AgentState


_PROMPT = """The previous search did not return enough information to answer
the user's question. Look at the original question and the chunks that were
retrieved. Produce ONE improved search query that is more likely to surface
the missing information. Reply with only the rewritten query, no quotes,
no explanation.

Original question: {query}

Retrieved chunks (may be partially relevant or off-topic):
{context}
"""


def rewriter_node(state: AgentState) -> dict:
    original = state.get("original_query") or state.get("query", "")
    nodes = state.get("retrieved_nodes") or []
    snippets = []
    for n in nodes[:5]:
        text = (n.get("text") or "")[:400]
        snippets.append(text)
    context = "\n---\n".join(snippets) or "(none)"

    llm = get_chat_llm()
    raw = llm.invoke([
        HumanMessage(content=_PROMPT.format(query=original, context=context))
    ]).content
    new_query = (raw if isinstance(raw, str) else str(raw)).strip()
    if not new_query:
        new_query = original
    # Keep original_query stable; only the working `query` is rewritten.
    return {"query": new_query, "attempts": (state.get("attempts") or 0) + 1}
