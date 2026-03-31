from __future__ import annotations

import csv
import importlib
import re
from io import StringIO
from pathlib import Path
from uuid import uuid4

from ai_butler.schemas import KnowledgeDocument


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_text(text: str, chunk_size: int = 650, overlap: int = 120) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    parts = re.split(r"(?<=[。！？；\n])", cleaned)
    chunks: list[str] = []
    current = ""
    for part in parts:
        if not part:
            continue
        if len(current) + len(part) <= chunk_size:
            current += part
            continue
        if current:
            chunks.append(current.strip())
        carry = current[-overlap:] if current else ""
        current = (carry + part).strip()
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def _extract_pdf(file_path: Path) -> str:
    pypdf = importlib.import_module("pypdf")
    reader = pypdf.PdfReader(str(file_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(file_path: Path) -> str:
    docx = importlib.import_module("docx")
    document = docx.Document(str(file_path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _extract_xlsx(file_path: Path) -> str:
    openpyxl = importlib.import_module("openpyxl")
    workbook = openpyxl.load_workbook(str(file_path), data_only=True)
    lines: list[str] = []
    for sheet in workbook.worksheets:
        lines.append(f"工作表:{sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            values = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
            if values:
                lines.append(" | ".join(values))
    return "\n".join(lines)


def _extract_csv(file_path: Path) -> str:
    rows = csv.reader(StringIO(file_path.read_text(encoding="utf-8", errors="ignore")))
    return "\n".join(" | ".join(cell.strip() for cell in row if cell.strip()) for row in rows if row)


def extract_text(file_path: Path) -> tuple[str, str]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(file_path), "pdf"
    if suffix == ".docx":
        return _extract_docx(file_path), "docx"
    if suffix == ".xlsx":
        return _extract_xlsx(file_path), "xlsx"
    if suffix == ".csv":
        return _extract_csv(file_path), "csv"
    return file_path.read_text(encoding="utf-8", errors="ignore"), "text"


def build_documents(file_path: Path, category: str, source: str) -> tuple[list[KnowledgeDocument], str]:
    raw_text, source_type = extract_text(file_path)
    chunks = split_text(raw_text)
    documents: list[KnowledgeDocument] = []
    for index, chunk in enumerate(chunks, start=1):
        documents.append(
            KnowledgeDocument(
                doc_id=f"doc-{uuid4().hex[:12]}-{index}",
                title=f"{file_path.stem}-片段-{index}",
                category=category,
                source=source,
                content=chunk,
                tags=[source_type, category],
            )
        )
    return documents, source_type
