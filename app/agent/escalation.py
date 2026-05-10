from app.agent.state import AgentState


def escalation_node(state: AgentState) -> dict:
    return {
        "answer": (
            "I cannot answer this confidently. A human operator will follow up. "
            "Please leave your contact details."
        ),
        "citations": [],
    }
