from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    doc_id: str
    title: str
    category: str
    source: str
    content: str
    tags: list[str] = Field(default_factory=list)


class RetrievalHit(BaseModel):
    title: str
    category: str
    score: float
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    llm_backend: str
    retrieval_backend: str
    references: list[RetrievalHit]


class IngestResponse(BaseModel):
    imported_count: int
    titles: list[str]
    vector_backend: str
    source_type: str


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


class HealthResponse(BaseModel):
    status: str
    llm_backend: str
    retrieval_backend: str
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    results: list[RetrievalHit]


class IngestPayload(BaseModel):
    category: str = "general"
    source: str = "企业内部资料"


class KnowledgeStats(BaseModel):
    total_documents: int
    categories: dict[str, int]
    backend: str


class QAContext(BaseModel):
    question: str
    chunks: list[RetrievalHit]
    metadata: dict[str, Any] = Field(default_factory=dict)
