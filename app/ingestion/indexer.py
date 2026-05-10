import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings as LISettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.agent.llm import get_embed_model
from app.config import settings
from app.ingestion.loader import load_directory
from app.retrieval.bm25_index import BM25Index


_COLLECTION = "rag_v2"


def _configure() -> None:
    LISettings.embed_model = get_embed_model()
    LISettings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)


def build_indexes() -> tuple[VectorStoreIndex, BM25Index]:
    _configure()

    docs = load_directory(settings.docs_dir)
    nodes = LISettings.node_parser.get_nodes_from_documents(docs)

    client = chromadb.PersistentClient(path=settings.chroma_path)
    try:
        client.delete_collection(_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(_COLLECTION)
    vstore = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vstore)

    vector_index = VectorStoreIndex(nodes, storage_context=storage_context)

    bm25 = BM25Index()
    bm25.build(nodes)

    return vector_index, bm25


def load_indexes() -> tuple[VectorStoreIndex, BM25Index]:
    _configure()

    client = chromadb.PersistentClient(path=settings.chroma_path)
    collection = client.get_or_create_collection(_COLLECTION)
    vstore = ChromaVectorStore(chroma_collection=collection)
    vector_index = VectorStoreIndex.from_vector_store(vector_store=vstore)

    bm25 = BM25Index()
    bm25.load()
    return vector_index, bm25
