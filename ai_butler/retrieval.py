from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter

from ai_butler.config import Settings
from ai_butler.schemas import KnowledgeDocument, RetrievalHit
from ai_butler.store import load_documents


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def build_char_ngrams(text: str, n: int = 3) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) <= n:
        return {compact} if compact else set()
    return {compact[index:index + n] for index in range(len(compact) - n + 1)}


class BaseRetriever(ABC):
    backend_name = "base"

    @abstractmethod
    def search(self, query: str, top_k: int = 4) -> list[RetrievalHit]:
        raise NotImplementedError

    @abstractmethod
    def refresh(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def category_stats(self) -> dict[str, int]:
        raise NotImplementedError

    def diagnostics(self) -> dict:
        return {"backend": self.backend_name}


class LocalVectorStore(BaseRetriever):
    backend_name = "本地混合向量库"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.refresh()

    @staticmethod
    def _join(doc: KnowledgeDocument) -> str:
        return " ".join([doc.title, doc.category, doc.source, " ".join(doc.tags), doc.content])

    def refresh(self) -> None:
        self.documents = load_documents(self.settings.docs_path)
        self.doc_text = {doc.doc_id: self._join(doc) for doc in self.documents}
        self.term_freq = {doc.doc_id: Counter(tokenize(self.doc_text[doc.doc_id])) for doc in self.documents}
        self.norm = {
            doc.doc_id: math.sqrt(sum(value * value for value in tf.values())) or 1.0
            for doc, tf in ((document, self.term_freq[document.doc_id]) for document in self.documents)
        }
        self.ngrams = {doc.doc_id: build_char_ngrams(self.doc_text[doc.doc_id]) for doc in self.documents}

    def search(self, query: str, top_k: int = 4) -> list[RetrievalHit]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_tf = Counter(query_tokens)
        query_norm = math.sqrt(sum(value * value for value in query_tf.values())) or 1.0
        query_ngrams = build_char_ngrams(query)
        candidates: list[tuple[KnowledgeDocument, float]] = []
        for doc in self.documents:
            tf = self.term_freq[doc.doc_id]
            lexical = sum(query_tf[token] * tf.get(token, 0) for token in query_tf) / (query_norm * self.norm[doc.doc_id])
            overlap = 0.08 * len(set(query_tokens) & set(tf.keys()))
            vector_like = len(query_ngrams & self.ngrams[doc.doc_id]) / max(len(query_ngrams | self.ngrams[doc.doc_id]), 1)
            rerank = 0.15 if query.lower() in self.doc_text[doc.doc_id].lower() else 0.0
            score = lexical * 0.55 + vector_like * 0.3 + overlap + rerank
            if score > 0:
                candidates.append((doc, score))
        candidates.sort(key=lambda item: item[1], reverse=True)
        return [
            RetrievalHit(title=doc.title, category=doc.category, score=round(score, 4), excerpt=doc.content[:160])
            for doc, score in candidates[:top_k]
        ]

    def count(self) -> int:
        return len(self.documents)

    def category_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for doc in self.documents:
            stats[doc.category] = stats.get(doc.category, 0) + 1
        return stats

    def diagnostics(self) -> dict:
        return {
            "backend": self.backend_name,
            "documents": len(self.documents),
            "mode": "local-hybrid",
        }


class MilvusRetriever(LocalVectorStore):
    backend_name = "Milvus向量库"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._store = None
        try:
            vectorstores_module = __import__("langchain_community.vectorstores", fromlist=["Milvus"])
            huggingface_module = __import__("langchain_huggingface", fromlist=["HuggingFaceEmbeddings"])
            self._milvus_cls = vectorstores_module.Milvus
            self._embeddings = huggingface_module.HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        except Exception as exc:
            raise RuntimeError("Milvus 所需依赖未安装。") from exc
        super().__init__(settings)

    def refresh(self) -> None:
        super().refresh()
        texts = [self._join(doc) for doc in self.documents]
        metadatas = [doc.model_dump() for doc in self.documents]
        self._store = self._milvus_cls.from_texts(
            texts=texts,
            embedding=self._embeddings,
            metadatas=metadatas,
            connection_args={"uri": self.settings.milvus_uri},
            collection_name="ai_butler_private_docs",
            drop_old=True,
        )

    def search(self, query: str, top_k: int = 4) -> list[RetrievalHit]:
        if self._store is None:
            return super().search(query, top_k)
        docs = self._store.similarity_search_with_score(query, k=max(top_k * 2, 6))
        hits: list[RetrievalHit] = []
        for document, score in docs[:top_k]:
            metadata = document.metadata
            hits.append(
                RetrievalHit(
                    title=metadata.get("title", "未知文档"),
                    category=metadata.get("category", "unknown"),
                    score=round(float(score), 4),
                    excerpt=metadata.get("content", "")[:160],
                )
            )
        return hits

    def diagnostics(self) -> dict:
        payload = {
            "backend": self.backend_name,
            "documents": len(self.documents),
            "milvus_uri": self.settings.milvus_uri,
            "connected": self._store is not None,
        }
        return payload


def build_retriever(settings: Settings) -> BaseRetriever:
    if settings.use_milvus:
        try:
            return MilvusRetriever(settings)
        except Exception:
            return LocalVectorStore(settings)
    return LocalVectorStore(settings)
