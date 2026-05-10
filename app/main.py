import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.supervisor import build_graph
from app.api.routes import router, set_graph
from app.config import settings
from app.ingestion.indexer import build_indexes, load_indexes
from app.retrieval.hybrid import HybridRetriever


def _init_graph() -> None:
    bm25_file = os.path.join(settings.bm25_path, "bm25.pkl")
    chroma_populated = (
        os.path.exists(settings.chroma_path) and bool(os.listdir(settings.chroma_path))
    )
    docs_present = (
        os.path.isdir(settings.docs_dir) and bool(os.listdir(settings.docs_dir))
    )

    if os.path.exists(bm25_file) and chroma_populated:
        vector_index, bm25 = load_indexes()
    elif docs_present:
        vector_index, bm25 = build_indexes()
    else:
        # No docs yet — load empty stores. Hybrid retrieval will return [].
        vector_index, bm25 = load_indexes()

    retriever = HybridRetriever(vector_index=vector_index, bm25=bm25)
    set_graph(build_graph(retriever))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.ensure_dirs()
    try:
        _init_graph()
    except Exception as e:
        # Graph stays None; endpoints will return 503. Log to stderr.
        import sys
        print(f"[startup] graph init failed: {e}", file=sys.stderr)
    yield


app = FastAPI(title="RAG Agent v2", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
