from unittest.mock import MagicMock, patch

from app.agent.clarification import clarification_agent


class _Resp:
    def __init__(self, content: str):
        self.content = content


@patch("app.agent.clarification.get_chat_llm")
def test_clarification_clear_query(mock_factory):
    llm = MagicMock()
    llm.invoke.return_value = _Resp("CLEAR")
    mock_factory.return_value = llm

    result = clarification_agent({"query": "What is the termination policy?"})
    assert result == {"needs_clarification": False, "clarification_question": None}


@patch("app.agent.clarification.get_chat_llm")
def test_clarification_ambiguous_query(mock_factory):
    llm = MagicMock()
    llm.invoke.return_value = _Resp(
        "I found several possible interpretations:\n1. Termination\n2. Duration\nWhich?"
    )
    mock_factory.return_value = llm

    result = clarification_agent({"query": "contract"})
    assert result["needs_clarification"] is True
    assert "Termination" in (result["clarification_question"] or "")


@patch("app.agent.clarification.get_chat_llm")
def test_clarification_clear_with_trailing_text(mock_factory):
    llm = MagicMock()
    llm.invoke.return_value = _Resp("CLEAR\n")
    mock_factory.return_value = llm

    result = clarification_agent({"query": "x"})
    assert result["needs_clarification"] is False
