import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from app.config import settings


_DDL = """
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    query TEXT,
    answer TEXT,
    sources TEXT,
    rating INTEGER,
    comment TEXT,
    created_at TEXT,
    improved INTEGER DEFAULT 0
)
"""


class FeedbackCollector:
    def __init__(self):
        self.db_path = settings.feedback_db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.execute(_DDL)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)

    def record(self, query: str, answer: str, sources, rating: int, comment: str = "") -> str:
        fid = str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (
                    fid,
                    query,
                    answer,
                    json.dumps(sources),
                    rating,
                    comment,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return fid

    def get_low_rated(self, limit: int = 20):
        with self._lock, self._connect() as conn:
            return conn.execute(
                "SELECT id, query, answer, sources, rating, comment, created_at "
                "FROM feedback WHERE rating < 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def get_stats(self) -> dict:
        with self._lock, self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            down = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating < 0").fetchone()[0]
            up = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating > 0").fetchone()[0]
        return {"total": total, "upvotes": up, "downvotes": down}
