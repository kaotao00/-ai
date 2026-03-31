from __future__ import annotations

import json
from pathlib import Path

from ai_butler.schemas import KnowledgeDocument


def load_documents(file_path: Path) -> list[KnowledgeDocument]:
    if not file_path.exists():
        return []
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    return [KnowledgeDocument(**item) for item in raw.get("documents", [])]


def save_documents(file_path: Path, documents: list[KnowledgeDocument]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"documents": [document.model_dump() for document in documents]}
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_documents(file_path: Path, new_documents: list[KnowledgeDocument]) -> int:
    documents = load_documents(file_path)
    documents.extend(new_documents)
    save_documents(file_path, documents)
    return len(new_documents)
