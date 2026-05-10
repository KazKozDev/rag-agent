from langchain_core.messages import HumanMessage

from app.agent.llm import get_chat_llm
from app.agent.state import AgentState


_PROMPT = """You are a strict gate. Decide if the user query can be sent to a
document search engine as-is. Default to CLEAR. Only mark AMBIGUOUS when the
query is a single bare noun (1-2 words) with no verb, question word, or
qualifier — i.e. truly impossible to search for.

Rules:
- Any query with a verb, question word (what/when/where/why/how/which), proper
  noun, or 4+ words → CLEAR.
- Single bare nouns like "contract", "payment", "pricing" → AMBIGUOUS.
- Greetings ("hello", "hi") → CLEAR (FAQ handles them).

Output format:
- If CLEAR → reply with exactly the single word: CLEAR
- If AMBIGUOUS → reply with 2-3 numbered clarifying options in the user's
  language, ending with "Which one did you mean?"

Query: {query}
"""


def clarification_agent(state: AgentState) -> dict:
    query = state.get("query", "")
    llm = get_chat_llm()
    result = llm.invoke([HumanMessage(content=_PROMPT.format(query=query))])
    raw = result.content
    response = (raw if isinstance(raw, str) else str(raw)).strip()

    if response.upper().startswith("CLEAR"):
        return {"needs_clarification": False, "clarification_question": None}
    return {"needs_clarification": True, "clarification_question": response}
