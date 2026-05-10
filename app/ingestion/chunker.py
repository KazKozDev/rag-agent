from llama_index.core.node_parser import SentenceSplitter


def chunk_documents(documents, chunk_size: int = 1024, chunk_overlap: int = 200):
    parser = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    nodes = parser.get_nodes_from_documents(documents)
    return nodes
