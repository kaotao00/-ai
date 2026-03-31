from __future__ import annotations

from pathlib import Path

from ai_butler.chain import PrivateQAChain
from ai_butler.config import Settings, load_settings
from ai_butler.ingestion import build_documents
from ai_butler.llm import build_llm
from ai_butler.retrieval import BaseRetriever, LocalVectorStore, build_retriever
from ai_butler.schemas import AskResponse, IngestResponse, KnowledgeStats, SearchResponse
from ai_butler.store import append_documents, load_documents


class PrivateAIAssistantService:
    def __init__(self, base_dir: Path | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings(base_dir)
        self.retriever = build_retriever(self.settings)
        self.llm = build_llm(self.settings)
        self.chain = PrivateQAChain(self.retriever, self.llm)

    def refresh(self) -> None:
        self.retriever.refresh()
        self.chain = PrivateQAChain(self.retriever, self.llm)

    def ask(self, question: str, top_k: int = 4) -> AskResponse:
        return self.chain.ask(question, top_k=top_k)

    def search(self, query: str, top_k: int = 5) -> SearchResponse:
        return SearchResponse(query=query, results=self.retriever.search(query, top_k=top_k))

    def ingest_file(self, file_path: Path, category: str, source: str) -> IngestResponse:
        documents, source_type = build_documents(file_path, category=category, source=source)
        count = append_documents(self.settings.docs_path, documents)
        self.refresh()
        return IngestResponse(
            imported_count=count,
            titles=[item.title for item in documents],
            vector_backend=self.retriever.backend_name,
            source_type=source_type,
        )

    def stats(self) -> KnowledgeStats:
        return KnowledgeStats(
            total_documents=self.retriever.count(),
            categories=self.retriever.category_stats(),
            backend=self.retriever.backend_name,
        )

    def diagnostics(self) -> dict:
        return {
            "llm": self.llm.diagnostics(),
            "retrieval": self.retriever.diagnostics(),
        }

    def list_documents(self, limit: int = 20) -> list[dict]:
        docs = load_documents(self.settings.docs_path)[:limit]
        return [
            {
                "title": doc.title,
                "category": doc.category,
                "source": doc.source,
                "preview": doc.content[:100],
            }
            for doc in docs
        ]


def build_local_service(base_dir: Path | None = None) -> PrivateAIAssistantService:
    settings = load_settings(base_dir)
    settings.use_milvus = False
    settings.use_ollama = False
    service = PrivateAIAssistantService(settings=settings)
    service.retriever = LocalVectorStore(settings)
    service.llm = build_llm(settings)
    service.chain = PrivateQAChain(service.retriever, service.llm)
    return service
