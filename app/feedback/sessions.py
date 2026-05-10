"""Tiny sqlite-backed session store for clarification continuation.

When clarification fires, we save (session_id, original_query) and return the
session_id to the client. On the next request the client passes session_id
back; the API merges the original query with the user's clarification answer
and resubmits. After consumption the row is deleted.

Lives next to feedback.db on the same volume. Same threading discipline:
check_same_thread=False, threading.Lock around writes.
"""
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

from app.config import settings


_DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    original_query TEXT NOT NULL,
    clarification_question TEXT,
    created_at TEXT NOT NULL
)
"""

# Sessions older than this are treated as expired and ignored on lookup.
TTL_MINUTES = 30


class SessionStore:
    def __init__(self):
        # Lives in the same directory as feedback.db.
        self.db_path = os.path.join(
            os.path.dirname(settings.feedback_db_path) or ".",
            "sessions.db",
        )
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.execute(_DDL)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)

    def create(self, original_query: str, clarification_question: str) -> str:
        sid = str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?)",
                (
                    sid,
                    original_query,
                    clarification_question,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return sid

    def consume(self, session_id: str) -> str | None:
        """Return the original query and delete the row. None if missing/expired."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT original_query, created_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            original_query, created_at = row
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
        try:
            ts = datetime.fromisoformat(created_at)
        except ValueError:
            return None
        if datetime.now(timezone.utc) - ts > timedelta(minutes=TTL_MINUTES):
            return None
        return original_query
