from llama_index.core.schema import NodeWithScore, TextNode

from app.retrieval.citation import format_citation, parse_citations


def _nws(metadata: dict) -> NodeWithScore:
    return NodeWithScore(node=TextNode(text="t", metadata=metadata), score=1.0)


def test_format_citation_with_page():
    assert format_citation(_nws({"file_name": "contract.pdf", "page_number": 12})) \
        == "[Source: contract.pdf, p. 12]"


def test_format_citation_without_page():
    out = format_citation(_nws({"file_name": "readme.txt"}))
    assert out == "[Source: readme.txt]"
    assert ", p." not in out


def test_format_citation_page_label_fallback():
    assert format_citation(_nws({"file_name": "manual.pdf", "page_label": "5"})) \
        == "[Source: manual.pdf, p. 5]"


def test_format_citation_accepts_bare_textnode():
    node = TextNode(text="t", metadata={"file_name": "x.pdf", "page_number": 3})
    assert format_citation(node) == "[Source: x.pdf, p. 3]"


def test_parse_citations_multiple():
    answer = (
        "This is stated clearly [Source: contract.pdf, p. 12]. "
        "Also see [Source: appendix.pdf, p. 45] for details."
    )
    citations = parse_citations(answer)
    assert citations == [
        "[Source: contract.pdf, p. 12]",
        "[Source: appendix.pdf, p. 45]",
    ]


def test_parse_citations_none():
    assert parse_citations("No citations here.") == []
