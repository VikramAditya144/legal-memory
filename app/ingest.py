"""
Document ingestion pipeline.

Orchestrates: parse → chunk → embed → store.
Supports WhatsApp .txt exports and PDF files.
"""

from pathlib import Path

from app.embeddings import embed_texts
from app.parsers.pdf import chunk_pdf
from app.parsers.whatsapp import chunk_messages, parse_whatsapp_export
from app.store import get_client as get_qdrant, upsert_chunks


def ingest_whatsapp(path: str | Path, progress_cb=None) -> dict:
    """
    Ingest a WhatsApp .txt export.

    progress_cb(step: str, pct: float) is called at key stages if provided.
    Returns {"chunks": int, "messages": int, "source": str}.
    """
    path = Path(path)
    source_name = path.stem  # e.g. "WhatsApp Chat with Acme Corp"

    if progress_cb:
        progress_cb("Parsing WhatsApp export…", 0.1)

    messages = parse_whatsapp_export(path)
    if not messages:
        return {"chunks": 0, "messages": 0, "source": source_name}

    chunks = chunk_messages(messages, window=5, overlap=1)

    # Tag source name into each chunk
    for c in chunks:
        c["metadata"]["source_name"] = source_name

    if progress_cb:
        progress_cb(f"Embedding {len(chunks)} chunks…", 0.4)

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    if progress_cb:
        progress_cb("Storing in Qdrant…", 0.8)

    qdrant_client = get_qdrant()
    stored = upsert_chunks(chunks, embeddings, qdrant_client)

    if progress_cb:
        progress_cb("Done.", 1.0)

    return {"chunks": stored, "messages": len(messages), "source": source_name}


def ingest_pdf(path: str | Path, progress_cb=None) -> dict:
    """
    Ingest a PDF file.

    Returns {"chunks": int, "pages": int, "source": str}.
    """
    path = Path(path)

    if progress_cb:
        progress_cb("Extracting PDF text…", 0.1)

    chunks = chunk_pdf(path)
    if not chunks:
        return {"chunks": 0, "pages": 0, "source": path.name}

    pages = max(
        (max(int(p) for p in str(c["metadata"].get("pages", "0")).split(", ") if p.isdigit())
         for c in chunks),
        default=0,
    )

    if progress_cb:
        progress_cb(f"Embedding {len(chunks)} chunks…", 0.4)

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    if progress_cb:
        progress_cb("Storing in Qdrant…", 0.8)

    qdrant_client = get_qdrant()
    stored = upsert_chunks(chunks, embeddings, qdrant_client)

    if progress_cb:
        progress_cb("Done.", 1.0)

    return {"chunks": stored, "pages": pages, "source": path.name}
