from langgraph.graph import StateGraph, END

from app.agent.clarification import clarification_agent
from app.agent.escalation import escalation_node
from app.agent.faq_agent import faq_node
from app.agent.query_analyzer import query_analyzer_node
from app.agent.rag_agent import make_rag_node
from app.agent.rewriter import rewriter_node
from app.agent.state import AgentState
from app.agent.validator import validator_node


MAX_REWRITE_ATTEMPTS = 2


def build_graph(retriever):
    g = StateGraph(AgentState)
    g.add_node("faq", faq_node)
    g.add_node("clarify", clarification_agent)
    g.add_node("analyze", query_analyzer_node)
    g.add_node("rag", make_rag_node(retriever))
    g.add_node("validate", validator_node)
    g.add_node("rewrite", rewriter_node)
    g.add_node("escalate", escalation_node)

    g.set_entry_point("faq")

    g.add_conditional_edges(
        "faq",
        lambda s: "done" if s.get("answer") else "needs_clarify",
        {"done": END, "needs_clarify": "clarify"},
    )

    g.add_conditional_edges(
        "clarify",
        lambda s: "ask_user" if s.get("needs_clarification") else "to_analyze",
        {"ask_user": END, "to_analyze": "analyze"},
    )

    g.add_edge("analyze", "rag")
    g.add_edge("rag", "validate")

    def _after_validate(s):
        if s.get("validated"):
            return "ok"
        if (s.get("attempts") or 0) < MAX_REWRITE_ATTEMPTS:
            return "retry"
        return "escalate"

    g.add_conditional_edges(
        "validate",
        _after_validate,
        {"ok": END, "retry": "rewrite", "escalate": "escalate"},
    )

    g.add_edge("rewrite", "rag")
    g.add_edge("escalate", END)

    return g.compile()
