from langchain_core.messages import HumanMessage

from app.agent.llm import get_chat_llm
from app.agent.state import AgentState


_PROMPT = """You are a fact-checker. Given the CONTEXT and an ANSWER, determine
whether every factual claim in the ANSWER is supported by the CONTEXT.
Reply with a single token: VALID or INVALID.

CONTEXT:
{context}

ANSWER:
{answer}
"""


def validator_node(state: AgentState) -> dict:
    answer = state.get("answer") or ""
    if not answer:
        return {"validated": False}

    context = "\n\n".join(n.get("text", "") for n in state.get("retrieved_nodes", []))
    llm = get_chat_llm()
    raw = llm.invoke([
        HumanMessage(content=_PROMPT.format(context=context or "(empty)", answer=answer))
    ]).content
    res = (raw if isinstance(raw, str) else str(raw)).strip().upper()
    return {"validated": res.startswith("VALID")}
