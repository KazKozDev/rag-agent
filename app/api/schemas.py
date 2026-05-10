from typing import List, Optional

from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    query: str = Field(min_length=1)
    # When the previous response asked for clarification, the client sends
    # the same session_id back along with the user's clarifying answer in
    # `query`. The server merges with the original query.
    session_id: Optional[str] = None


class AnswerSchema(BaseModel):
    answer: str
    citations: List[str]
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    # Set only when needs_clarification=True. Echo back to /api/query.
    session_id: Optional[str] = None


class FeedbackSchema(BaseModel):
    query: str
    answer: str
    sources: List[str]
    rating: int  # 1 = up, -1 = down
    comment: Optional[str] = ""


class StatsSchema(BaseModel):
    total: int
    upvotes: int
    downvotes: int


class DocumentInfo(BaseModel):
    name: str
    size_bytes: int


class DocumentsSchema(BaseModel):
    documents: List[DocumentInfo]
    indexed_count: int
    store: str


class IngestResponse(BaseModel):
    ok: bool
    indexed_count: int
