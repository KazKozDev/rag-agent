"""RAG node with tool-use.

The model is given a `search` tool that hits HybridRetriever. It can call it
1..MAX_TOOL_CALLS times before producing a final answer. This matters for
compound questions ("compare X and Y") where one retrieve can't surface both.

We accumulate every retrieved node across tool calls and pass the union to
the validator unchanged.
"""
from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool

from app.agent.llm import get_chat_llm
from app.agent.state import AgentState
from app.retrieval.citation import format_citation, parse_citations


_SYS = (
    "You are a precise assistant that answers from indexed documents. "
    "Use the `search` tool to fetch passages. For compound or multi-part "
    "questions, run search MULTIPLE TIMES with focused sub-queries — one "
    "per topic — instead of a single broad query. "
    "After every factual claim in your answer, append the matching "
    "[Source: ...] citation exactly as written in the search results. "
    "If the answer is not in the retrieved passages, say so explicitly. "
    "Reply in the same language as the question."
)

MAX_TOOL_CALLS = 4


def _serialize_node(n) -> dict:
    return {
        "id": n.node.node_id,
        "text": n.node.get_content(),
        "metadata": dict(n.node.metadata or {}),
        "score": n.score,
    }


def make_rag_node(retriever):
    def rag_node(state: AgentState) -> dict:
        query = state.get("query", "")
        filters = state.get("metadata_filters") or None

        collected_nodes: list[dict] = []
        seen_ids: set[str] = set()

        def _ingest(nodes):
            blocks = []
            for n in nodes:
                cite = format_citation(n)
                blocks.append(f"{cite}\n{n.node.get_content()}")
                if n.node.node_id not in seen_ids:
                    seen_ids.add(n.node.node_id)
                    collected_nodes.append(_serialize_node(n))
            return "\n\n---\n\n".join(blocks) or "(no results)"

        @tool
        def search(query: str) -> str:
            """Search the indexed documents. Returns top passages each prefixed
            with its [Source: ...] citation tag. Run multiple times with
            different focused sub-queries for compound questions."""
            return _ingest(retriever.retrieve(query, filters=filters))

        llm = get_chat_llm().bind_tools([search])

        messages: list[Any] = [
            SystemMessage(content=_SYS),
            HumanMessage(content=query),
        ]

        # Prime with the obvious first retrieve so a model that ignores the
        # tool still gets some context.
        primer = _ingest(retriever.retrieve(query, filters=filters))
        if primer != "(no results)":
            messages.append(
                HumanMessage(
                    content="Initial search results:\n\n" + primer +
                    "\n\nIf this is not enough (e.g. the question has multiple "
                    "parts), call the `search` tool with focused sub-queries. "
                    "Otherwise answer now."
                )
            )

        answer = ""
        for _ in range(MAX_TOOL_CALLS + 1):
            ai = llm.invoke(messages)
            messages.append(ai)
            tool_calls = getattr(ai, "tool_calls", None) or []
            if not tool_calls:
                raw = ai.content
                answer = raw if isinstance(raw, str) else str(raw)
                break
            for tc in tool_calls:
                args = tc.get("args") or {}
                tool_query = args.get("query", "")
                try:
                    result = search.invoke({"query": tool_query})
                except Exception as e:  # noqa: BLE001
                    result = f"(search failed: {e})"
                messages.append(
                    ToolMessage(content=result, tool_call_id=tc.get("id", ""))
                )

        # If tool budget ran out, force a final answer with no tools bound.
        if not answer:
            final = get_chat_llm().invoke(messages + [
                HumanMessage(content="Tool budget exhausted. Answer now from "
                             "what you have, or say you don't have enough info.")
            ])
            raw = final.content
            answer = raw if isinstance(raw, str) else str(raw)

        return {
            "answer": answer,
            "citations": parse_citations(answer),
            "retrieved_nodes": collected_nodes,
        }

    return rag_node
