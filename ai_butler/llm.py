from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from ai_butler.config import Settings
from ai_butler.schemas import RetrievalHit


class BaseLLM(ABC):
    backend_name = "mock"

    @abstractmethod
    def answer(self, question: str, references: list[RetrievalHit]) -> str:
        raise NotImplementedError

    def diagnostics(self) -> dict:
        return {"backend": self.backend_name}


class MockLLM(BaseLLM):
    backend_name = "本地模板回答"

    def answer(self, question: str, references: list[RetrievalHit]) -> str:
        if not references:
            return "当前知识库中未检索到足够相关的企业资料，建议补充制度、流程或项目文档后再提问。"
        snippets = "；".join(f"《{item.title}》提到：{item.excerpt}" for item in references[:3])
        return f"根据已检索到的企业内部资料，针对“{question}”的回答如下：{snippets}。建议在正式业务场景中结合最新制度版本进行复核。"


class OllamaLLM(BaseLLM):
    backend_name = "Ollama本地模型"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def diagnostics(self) -> dict:
        payload = {
            "backend": self.backend_name,
            "configured": True,
            "base_url": self.settings.ollama_base_url,
            "model": self.settings.ollama_model,
            "reachable": False,
            "model_available": False,
        }
        try:
            tags_resp = requests.get(f"{self.settings.ollama_base_url}/api/tags", timeout=10)
            tags_resp.raise_for_status()
            payload["reachable"] = True
            models = tags_resp.json().get("models", [])
            payload["available_models"] = [item.get("name", "") for item in models]
            payload["model_available"] = any(item.get("name") == self.settings.ollama_model for item in models)
        except Exception as exc:
            payload["error"] = str(exc)
        return payload

    def answer(self, question: str, references: list[RetrievalHit]) -> str:
        prompt = self._build_prompt(question, references)
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={"model": self.settings.ollama_model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            payload = response.json()
            text = payload.get("response", "").strip()
            if text:
                return text
        except Exception:
            pass
        return MockLLM().answer(question, references)

    @staticmethod
    def _build_prompt(question: str, references: list[RetrievalHit]) -> str:
        context = "\n".join(f"- {item.title}: {item.excerpt}" for item in references)
        return (
            "你是企业内部 AI 管家，请严格基于提供的内部知识回答，不能编造不存在的制度或数据。\n"
            f"问题：{question}\n"
            f"参考资料：\n{context}\n"
            "请用中文给出结构化、简洁、可信的回答，并在结尾说明回答依据来自内部知识库。"
        )


def build_llm(settings: Settings) -> BaseLLM:
    if settings.use_ollama:
        return OllamaLLM(settings)
    return MockLLM()
