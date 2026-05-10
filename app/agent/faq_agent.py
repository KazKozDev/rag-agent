import re

from app.agent.state import AgentState


FAQ = {
    "hello": "Hi! Ask me anything about the indexed documents.",
    "hi": "Hi! Ask me anything about the indexed documents.",
    "help": "Send a question. I will retrieve relevant passages and answer with citations.",
    "price": "Tiers: Basic $1,500, Standard $3,500, Enterprise $6,000.",
    "pricing": "Tiers: Basic $1,500, Standard $3,500, Enterprise $6,000.",
}


def faq_node(state: AgentState) -> dict:
    q = state.get("query", "").lower().strip()
    for key, ans in FAQ.items():
        if re.search(rf"\b{re.escape(key)}\b", q):
            return {"answer": ans, "citations": []}
    return {"answer": "", "citations": []}
