from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ai_butler.api_service import PrivateAIAssistantService
from ai_butler.config import load_settings
from ai_butler.schemas import AskRequest, AskResponse, HealthResponse, IngestResponse, KnowledgeStats, SearchResponse


def create_app(base_dir: Path | None = None) -> FastAPI:
    settings = load_settings(base_dir)
    service = PrivateAIAssistantService(settings=settings)

    app = FastAPI(title="AI管家私有化问答系统", version="1.0.0")

    if settings.static_dir.exists():
        app.mount("/assets", StaticFiles(directory=settings.static_dir), name="assets")

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            llm_backend=service.llm.backend_name,
            retrieval_backend=service.retriever.backend_name,
            diagnostics=service.diagnostics(),
        )

    @app.get("/stats", response_model=KnowledgeStats)
    def stats() -> KnowledgeStats:
        return service.stats()

    @app.get("/search", response_model=SearchResponse)
    def search(query: str = Query(...), top_k: int = Query(default=5)) -> SearchResponse:
        return service.search(query=query, top_k=top_k)

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        return service.ask(question=request.question, top_k=request.top_k)

    @app.post("/ingest", response_model=IngestResponse)
    def ingest(
        file: UploadFile = File(...),
        category: str = Form(default="general"),
        source: str = Form(default="企业内部资料"),
    ) -> IngestResponse:
        upload_dir = settings.base_dir / "uploads"
        upload_dir.mkdir(exist_ok=True)
        filename = file.filename or "uploaded.txt"
        target_path = upload_dir / filename
        with target_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
        return service.ingest_file(file_path=target_path, category=category, source=source)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(settings.static_dir / "index.html")

    return app
