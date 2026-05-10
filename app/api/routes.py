import os
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.api.schemas import (
    AnswerSchema,
    DocumentInfo,
    DocumentsSchema,
    FeedbackSchema,
    IngestResponse,
    QuerySchema,
    StatsSchema,
)
from app.config import settings
from app.feedback.collector import FeedbackCollector
from app.feedback.reporter import weekly_report
from app.feedback.sessions import SessionStore

router = APIRouter()
feedback_collector = FeedbackCollector()
session_store = SessionStore()

_GRAPH = {"graph": None}


def set_graph(graph) -> None:
    _GRAPH["graph"] = graph


def _safe_doc_path(filename: str) -> str:
    if not filename or os.path.basename(filename) != filename:
        raise HTTPException(400, "Invalid filename")
    docs_dir = os.path.abspath(settings.docs_dir)
    path = os.path.abspath(os.path.join(docs_dir, filename))
    if not path.startswith(docs_dir + os.sep):
        raise HTTPException(400, "Invalid filename")
    return path


def _reload_graph_from_current_docs() -> int:
    from app.agent.supervisor import build_graph
    from app.ingestion.indexer import build_indexes, load_indexes
    from app.retrieval.bm25_index import BM25Index
    from app.retrieval.hybrid import HybridRetriever

    docs_present = (
        os.path.isdir(settings.docs_dir)
        and any(os.path.isfile(os.path.join(settings.docs_dir, name)) for name in os.listdir(settings.docs_dir))
    )
    if docs_present:
        vector_index, bm25 = build_indexes()
        # See note in /api/ingest: count via chroma, not the in-memory docstore.
        count = 0
        try:
            import chromadb
            client = chromadb.PersistentClient(path=settings.chroma_path)
            colls = client.list_collections()
            if colls:
                name = colls[0] if isinstance(colls[0], str) else colls[0].name
                count = client.get_collection(name).count()
        except Exception:
            pass
    else:
        import chromadb

        client = chromadb.PersistentClient(path=settings.chroma_path)
        try:
            client.delete_collection("rag_v2")
        except Exception:
            pass
        BM25Index().build([])
        vector_index, bm25 = load_indexes()
        count = 0
    set_graph(build_graph(HybridRetriever(vector_index=vector_index, bm25=bm25)))
    return count


@router.post("/api/query", response_model=AnswerSchema)
async def query(payload: QuerySchema):
    graph = _GRAPH["graph"]
    if graph is None:
        raise HTTPException(503, "Graph not initialized")

    user_query = payload.query

    # If the client is answering a prior clarification, splice the original
    # query back in. Combined query is long enough that the clarify gate
    # will pass it through (clarify defaults to CLEAR for 4+ word inputs).
    if payload.session_id:
        original = session_store.consume(payload.session_id)
        if original:
            user_query = f"{original} — {payload.query}"

    try:
        state = graph.invoke({"query": user_query, "original_query": user_query})
    except Exception as e:
        raise HTTPException(500, f"Graph error: {e}")

    new_session_id = None
    if state.get("needs_clarification"):
        new_session_id = session_store.create(
            original_query=user_query,
            clarification_question=state.get("clarification_question") or "",
        )

    return AnswerSchema(
        answer=state.get("answer", "") or "",
        citations=state.get("citations", []) or [],
        needs_clarification=bool(state.get("needs_clarification")),
        clarification_question=state.get("clarification_question"),
        session_id=new_session_id,
    )


@router.post("/api/feedback")
async def record_feedback(fb: FeedbackSchema):
    fid = feedback_collector.record(
        query=fb.query,
        answer=fb.answer,
        sources=fb.sources,
        rating=fb.rating,
        comment=fb.comment or "",
    )
    return {"ok": True, "feedback_id": fid}


@router.get("/api/feedback/stats", response_model=StatsSchema)
async def feedback_stats():
    return feedback_collector.get_stats()


@router.get("/api/feedback/report")
async def feedback_report():
    return {"report": weekly_report()}


@router.get("/api/documents", response_model=DocumentsSchema)
async def list_documents():
    docs_dir = settings.docs_dir
    os.makedirs(docs_dir, exist_ok=True)
    files = []
    for name in sorted(os.listdir(docs_dir)):
        fp = os.path.join(docs_dir, name)
        if os.path.isfile(fp):
            files.append(DocumentInfo(name=name, size_bytes=os.path.getsize(fp)))
    import chromadb
    count = 0
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        colls = client.list_collections()
        if colls:
            name = colls[0] if isinstance(colls[0], str) else colls[0].name
            count = client.get_collection(name).count()
    except Exception:
        pass
    return DocumentsSchema(documents=files, indexed_count=count, store="chroma")


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename")
    ext = os.path.splitext(file.filename)[1].lower()
    allowed = {".pdf", ".csv", ".md", ".txt", ".html", ".htm", ".json", ".docx"}
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}")
    MAX_SIZE = 200 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "File exceeds 200MB limit")
    os.makedirs(settings.docs_dir, exist_ok=True)
    dest = os.path.join(settings.docs_dir, file.filename)
    with open(dest, "wb") as f:
        f.write(content)
    return {"ok": True, "filename": file.filename, "size_bytes": len(content)}


@router.delete("/api/documents/{filename:path}")
async def delete_document(filename: str):
    path = _safe_doc_path(filename)
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(404, "Document not found")
    try:
        os.remove(path)
        indexed_count = _reload_graph_from_current_docs()
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    return {"ok": True, "filename": filename, "indexed_count": indexed_count}


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest():
    from app.agent.supervisor import build_graph
    from app.ingestion.indexer import build_indexes
    from app.retrieval.hybrid import HybridRetriever

    try:
        vector_index, bm25 = build_indexes()
    except Exception as e:
        raise HTTPException(500, f"Indexing failed: {e}")
    retriever = HybridRetriever(vector_index=vector_index, bm25=bm25)
    set_graph(build_graph(retriever))
    # ChromaVectorStore stores chunks in chroma, not in the in-memory docstore,
    # so vector_index.docstore.docs is empty here. Count via the collection.
    count = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_path)
        colls = client.list_collections()
        if colls:
            name = colls[0] if isinstance(colls[0], str) else colls[0].name
            count = client.get_collection(name).count()
    except Exception:
        pass
    return IngestResponse(ok=True, indexed_count=count)


@router.get("/api/health")
async def health():
    return {"ok": True}
