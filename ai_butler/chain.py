from __future__ import annotations

from ai_butler.llm import BaseLLM
from ai_butler.retrieval import BaseRetriever
from ai_butler.schemas import AskResponse


class PrivateQAChain:
    def __init__(self, retriever: BaseRetriever, llm: BaseLLM) -> None:
        self.retriever = retriever
        self.llm = llm

    def ask(self, question: str, top_k: int = 4) -> AskResponse:
        hits = self.retriever.search(question, top_k=top_k)
        answer = self.llm.answer(question, hits)
        return AskResponse(
            question=question,
            answer=answer,
            llm_backend=self.llm.backend_name,
            retrieval_backend=self.retriever.backend_name,
            references=hits,
        )
