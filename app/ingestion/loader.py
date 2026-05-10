import os

import fitz  # PyMuPDF
from llama_index.core import Document, SimpleDirectoryReader


def load_pdf_with_pages(filepath: str) -> list[Document]:
    doc = fitz.open(filepath)
    out: list[Document] = []
    try:
        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")
            if not isinstance(text, str) or not text.strip():
                continue
            out.append(Document(
                text=text,
                metadata={
                    "file_name": os.path.basename(filepath),
                    "page_number": page_num + 1,
                    "page_label": str(page_num + 1),
                    "file_path": filepath,
                },
            ))
    finally:
        doc.close()
    return out


def load_directory(dir_path: str) -> list[Document]:
    """Load every file in dir_path. PDFs are split per page via PyMuPDF;
    everything else falls back to SimpleDirectoryReader."""
    if not os.path.isdir(dir_path):
        return []

    pdfs: list[str] = []
    others: list[str] = []
    for name in os.listdir(dir_path):
        full = os.path.join(dir_path, name)
        if not os.path.isfile(full):
            continue
        (pdfs if name.lower().endswith(".pdf") else others).append(full)

    docs: list[Document] = []
    for pdf in pdfs:
        docs.extend(load_pdf_with_pages(pdf))
    if others:
        reader = SimpleDirectoryReader(input_files=others)
        for d in reader.load_data():
            if "file_name" not in d.metadata:
                d.metadata["file_name"] = os.path.basename(
                    d.metadata.get("file_path", "unknown")
                )
            docs.append(d)
    return docs
