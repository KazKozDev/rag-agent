import os
import tempfile

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _tmp_data(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "data_dir", d)
    monkeypatch.setattr(settings, "docs_dir", os.path.join(d, "docs"))
    monkeypatch.setattr(settings, "chroma_path", os.path.join(d, "chroma"))
    monkeypatch.setattr(settings, "bm25_path", os.path.join(d, "bm25"))
    monkeypatch.setattr(settings, "feedback_db_path", os.path.join(d, "feedback.db"))
    for sub in ("docs", "chroma", "bm25"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    yield d
