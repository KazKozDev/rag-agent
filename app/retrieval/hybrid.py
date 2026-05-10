from typing import Any, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore, TextNode

from app.config import settings
from app.retrieval.bm25_index import BM25Index


def rrf(results_vector, results_bm25, k: int = 60, top_k: int = 5):
    """Reciprocal Rank Fusion. Returns [(doc_id, fused_score), ...]."""
    scores: dict[str, float] = {}
    for rank, nws in enumerate(results_vector):
        doc_id = nws.node.node_id
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    for rank, item in enumerate(results_bm25):
        doc_id = item["doc"]["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])[:top_k]


def _meta_match(metadata: dict, filters: dict) -> bool:
    """Every filter key must equal the corresponding metadata value.
    page_number compared as int, file_name case-insensitive."""
    for k, v in filters.items():
        mv = metadata.get(k)
        if mv is None:
            return False
        if k == "page_number":
            try:
                if int(mv) != int(v):
                    return False
            except (TypeError, ValueError):
                return False
        elif k == "file_name":
            if str(mv).lower() != str(v).lower():
                return False
        else:
            if mv != v:
                return False
    return True


class HybridRetriever:
    def __init__(self, vector_index: VectorStoreIndex, bm25: BM25Index):
        if vector_index is None:
            raise ValueError("vector_index is required")
        self.vector_index = vector_index
        self.bm25 = bm25

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[NodeWithScore]:
        top_k = top_k or settings.top_k

        vector_results: list[NodeWithScore] = (
            self.vector_index.as_retriever(similarity_top_k=top_k * 2).retrieve(query)
        )
        bm25_results = self.bm25.retrieve(query, top_k=top_k * 2)

        # Post-filter on metadata. Wider initial window (top_k * 2) keeps us
        # from emptying the result set after filtering in most cases.
        if filters:
            vector_results = [
                nws for nws in vector_results
                if _meta_match(dict(nws.node.metadata or {}), filters)
            ]
            bm25_results = [
                item for item in bm25_results
                if _meta_match(item["doc"].get("metadata") or {}, filters)
            ]

        node_map: dict[str, NodeWithScore] = {}
        for nws in vector_results:
            node_map[nws.node.node_id] = nws
        for item in bm25_results:
            doc = item["doc"]
            if doc["id"] in node_map:
                continue
            tn = TextNode(text=doc["text"], id_=doc["id"], metadata=doc["metadata"])
            node_map[doc["id"]] = NodeWithScore(node=tn, score=item["score"])

        fused = rrf(vector_results, bm25_results, k=settings.rrf_k, top_k=top_k)
        return [node_map[doc_id] for doc_id, _ in fused if doc_id in node_map]
