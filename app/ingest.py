"""
Document ingestion pipeline.

Orchestrates: parse → chunk → store in Supermemory.
Supports WhatsApp .txt exports and PDF files.
"""

from pathlib import Path

from app.parsers.pdf import chunk_pdf
from app.parsers.whatsapp import chunk_messages, parse_whatsapp_export
import app.supermemory as supermemory


def ingest_whatsapp(path: str | Path, progress_cb=None, source_name: str | None = None) -> dict:
    """
    Ingest a WhatsApp .txt export into Supermemory.

    progress_cb(step: str, pct: float) is called at key stages if provided.
    Returns {"chunks": int, "messages": int, "source": str}.
    """
    path = Path(path)
    source_name = source_name or path.stem

    if progress_cb:
        progress_cb("Parsing WhatsApp export…", 0.1)

    messages = parse_whatsapp_export(path)
    if not messages:
        return {"chunks": 0, "messages": 0, "source": source_name}

    chunks = chunk_messages(messages, window=5, overlap=1)
    for c in chunks:
        c["metadata"]["source_name"] = source_name

    if progress_cb:
        progress_cb(f"Uploading {len(chunks)} chunks to Supermemory…", 0.4)

    stored = supermemory.add_chunks(chunks)

    if progress_cb:
        progress_cb("Done.", 1.0)

    return {"chunks": stored, "messages": len(messages), "source": source_name}


def ingest_pdf(path: str | Path, progress_cb=None, source_name: str | None = None) -> dict:
    """
    Ingest a PDF file into Supermemory.

    Returns {"chunks": int, "pages": int, "source": str}.
    """
    path = Path(path)
    display_name = source_name or path.name

    if progress_cb:
        progress_cb("Extracting PDF text…", 0.1)

    chunks = chunk_pdf(path)
    if not chunks:
        return {"chunks": 0, "pages": 0, "source": display_name}

    for c in chunks:
        c["metadata"]["source_name"] = display_name

    all_page_nums = [p for c in chunks for p in c["metadata"].get("pages", [])]
    pages = max(all_page_nums) if all_page_nums else 0

    if progress_cb:
        progress_cb(f"Uploading {len(chunks)} chunks to Supermemory…", 0.4)

    stored = supermemory.add_chunks(chunks)

    if progress_cb:
        progress_cb("Done.", 1.0)

    return {"chunks": stored, "pages": pages, "source": display_name}
