from llama_index.core.schema import NodeWithScore, TextNode

from app.retrieval.hybrid import HybridRetriever, rrf


def test_rrf_empty():
    assert rrf([], [], top_k=5) == []


def test_rrf_ordering():
    n1 = TextNode(text="doc one", id_="id1")
    n2 = TextNode(text="doc two", id_="id2")
    n3 = TextNode(text="doc three", id_="id3")

    vector_results = [
        NodeWithScore(node=n1, score=0.9),
        NodeWithScore(node=n2, score=0.8),
        NodeWithScore(node=n3, score=0.5),
    ]
    bm25_results = [
        {"doc": {"id": "id2", "text": "doc two", "metadata": {}}, "score": 0.7},
        {"doc": {"id": "id1", "text": "doc one", "metadata": {}}, "score": 0.6},
    ]

    fused = rrf(vector_results, bm25_results, top_k=3)
    ids = [doc_id for doc_id, _ in fused]
    # id1 (rank 0 vector + rank 1 bm25) and id2 (rank 1 vector + rank 0 bm25)
    # both have the same score; id3 (rank 2 vector only) is lowest.
    assert ids[2] == "id3"
    assert set(ids[:2]) == {"id1", "id2"}


def test_rrf_top_k_limit():
    nodes = [TextNode(text=f"doc {i}", id_=f"id{i}") for i in range(10)]
    vector_results = [NodeWithScore(node=n, score=0.9) for n in nodes]
    fused = rrf(vector_results, [], top_k=3)
    assert len(fused) == 3


class _StubRetriever:
    def __init__(self, results):
        self._results = results

    def retrieve(self, _query):
        return self._results


class _StubVectorIndex:
    def __init__(self, results):
        self._results = results

    def as_retriever(self, **_kwargs):
        return _StubRetriever(self._results)


class _StubBM25:
    def __init__(self, results):
        self._results = results

    def retrieve(self, _query, top_k=10):
        return self._results[:top_k]


def test_hybrid_metadata_filter_drops_non_matching():
    keep = TextNode(text="keep me", id_="k1",
                    metadata={"file_name": "want.pdf", "page_number": 4})
    drop1 = TextNode(text="other file", id_="d1",
                     metadata={"file_name": "other.pdf", "page_number": 4})
    drop2 = TextNode(text="other page", id_="d2",
                     metadata={"file_name": "want.pdf", "page_number": 9})
    vector_results = [
        NodeWithScore(node=keep, score=0.9),
        NodeWithScore(node=drop1, score=0.85),
        NodeWithScore(node=drop2, score=0.8),
    ]
    bm25_results = [
        {"doc": {"id": "b1", "text": "bm25 hit",
                 "metadata": {"file_name": "want.pdf", "page_number": 4}},
         "score": 5.0},
        {"doc": {"id": "b2", "text": "bm25 wrong page",
                 "metadata": {"file_name": "want.pdf", "page_number": 1}},
         "score": 4.0},
    ]
    retriever = HybridRetriever(
        vector_index=_StubVectorIndex(vector_results),
        bm25=_StubBM25(bm25_results),
    )
    out = retriever.retrieve(
        "anything",
        top_k=5,
        filters={"file_name": "WANT.PDF", "page_number": 4},
    )
    ids = {nws.node.node_id for nws in out}
    assert ids == {"k1", "b1"}


def test_hybrid_includes_bm25_only_documents():
    """Regression for v1 bug where BM25-only hits were silently dropped."""
    vec_node = TextNode(text="vector hit", id_="v1", metadata={"file_name": "v.pdf"})
    vector_results = [NodeWithScore(node=vec_node, score=0.9)]
    bm25_results = [
        {"doc": {"id": "b1", "text": "bm25 hit", "metadata": {"file_name": "b.pdf"}},
         "score": 5.0},
    ]

    retriever = HybridRetriever(
        vector_index=_StubVectorIndex(vector_results),
        bm25=_StubBM25(bm25_results),
    )
    out = retriever.retrieve("anything", top_k=5)
    ids = {nws.node.node_id for nws in out}
    assert "v1" in ids
    assert "b1" in ids, "BM25-only document missing from fused output"
