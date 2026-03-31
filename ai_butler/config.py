from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    base_dir: Path
    data_dir: Path
    docs_path: Path
    static_dir: Path
    use_ollama: bool
    ollama_base_url: str
    ollama_model: str
    use_milvus: bool
    milvus_uri: str


def load_settings(base_dir: Path | None = None) -> Settings:
    root = (base_dir or Path(__file__).resolve().parents[1]).resolve()
    data_dir = root / "data"
    return Settings(
        base_dir=root,
        data_dir=data_dir,
        docs_path=data_dir / "knowledge_docs.json",
        static_dir=root / "frontend",
        use_ollama=os.getenv("AI_BUTLER_USE_OLLAMA", "0") == "1",
        ollama_base_url=os.getenv("AI_BUTLER_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("AI_BUTLER_OLLAMA_MODEL", "qwen2.5:7b"),
        use_milvus=os.getenv("AI_BUTLER_USE_MILVUS", "0") == "1",
        milvus_uri=os.getenv("AI_BUTLER_MILVUS_URI", "http://localhost:19530"),
    )
