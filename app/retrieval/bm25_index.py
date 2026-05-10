import os
import pickle
import re

from rank_bm25 import BM25Okapi

from app.config import settings


_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self):
        os.makedirs(settings.bm25_path, exist_ok=True)
        self.index_path = os.path.join(settings.bm25_path, "bm25.pkl")
        self.bm25: BM25Okapi | None = None
        self.documents: list[dict] = []

    def build(self, nodes) -> None:
        tokenized = [tokenize(n.text) for n in nodes]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None
        self.documents = [
            {"id": n.node_id, "text": n.text, "metadata": dict(n.metadata or {})}
            for n in nodes
        ]
        self._save()

    def retrieve(self, query: str, top_k: int = 10) -> list[dict]:
        if not self.bm25 or not self.documents:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{"doc": self.documents[i], "score": float(scores[i])} for i in top]

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "documents": self.documents}, f)

    def load(self) -> bool:
        if not os.path.exists(self.index_path):
            return False
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.documents = data["documents"]
        return True
