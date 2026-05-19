"""
Supermemory — primary storage and retrieval layer.

Replaces Qdrant as the sole vector store. Handles ingest, search, and
collection stats via the Supermemory cloud API.

Container tags:
  legal-pdf        → PDF documents
  legal-whatsapp   → WhatsApp chat exports
"""

from __future__ import annotations

import os
from functools import lru_cache

_CONTAINER_PDF = "legal-pdf"
_CONTAINER_WHATSAPP = "legal-whatsapp"


@lru_cache(maxsize=1)
def _get_client():
    try:
        from supermemory import Supermemory
    except ImportError:
        return None
    api_key = os.getenv("SUPERMEMORY_API_KEY", "")
    if not api_key:
        return None
    return Supermemory(api_key=api_key)


def is_available() -> bool:
    return _get_client() is not None


def add_chunks(chunks: list[dict]) -> int:
    """
    Push ingested chunks to Supermemory.

    Each chunk must have "text" and "metadata" keys (same shape as
    produced by chunk_pdf / chunk_messages).  Returns count stored.
    Raises if Supermemory is unavailable.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(
            "Supermemory is not configured. Set SUPERMEMORY_API_KEY in your environment."
        )

    stored = 0
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source_type = meta.get("source_type", "pdf")
        container = _CONTAINER_WHATSAPP if source_type == "whatsapp" else _CONTAINER_PDF

        sm_meta: dict = {
            "source_name": str(meta.get("source_name", "")),
            "source_type": source_type,
        }
        if meta.get("pages"):
            sm_meta["pages"] = str(meta["pages"])
        if meta.get("start_time"):
            sm_meta["start_time"] = str(meta["start_time"])
        if meta.get("senders"):
            sm_meta["senders"] = str(meta["senders"])

        client.documents.add(
            content=chunk["text"],
            container_tag=container,
            metadata=sm_meta,
            task_type="superrag",
        )
        stored += 1

    return stored


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search Supermemory and return results in a normalised shape.
    Returns [] if Supermemory is unavailable.
    """
    client = _get_client()
    if client is None:
        return []

    try:
        response = client.search.documents(
            q=query,
            container_tags=[_CONTAINER_PDF, _CONTAINER_WHATSAPP],
            limit=top_k,
            rerank=True,
            rewrite_query=True,
            chunk_threshold=0.3,
        )
    except Exception:
        return []

    results = []
    for doc in getattr(response, "results", []):
        chunks = getattr(doc, "chunks", [])
        text = chunks[0].content if chunks else getattr(doc, "content", "")
        score = getattr(chunks[0], "score", 0.0) if chunks else 0.0
        metadata = getattr(doc, "metadata", {}) or {}

        results.append({
            "score": round(float(score), 3),
            "text": text or "",
            "source_type": metadata.get("source_type", ""),
            "source_name": metadata.get("source_name", ""),
            "start_time": metadata.get("start_time", ""),
            "pages": metadata.get("pages", ""),
            "senders": metadata.get("senders", ""),
        })

    return results


def collection_stats() -> dict:
    """
    Return stats derived from Supermemory document listings.
    Falls back to zeroed stats if the API is unavailable.
    """
    client = _get_client()
    if client is None:
        return {"total_chunks": 0, "pdf_sources": [], "whatsapp_sources": [], "supermemory_available": False}

    pdf_sources: set[str] = set()
    whatsapp_sources: set[str] = set()
    total = 0

    for container, bucket in (
        (_CONTAINER_PDF, pdf_sources),
        (_CONTAINER_WHATSAPP, whatsapp_sources),
    ):
        try:
            page = 1
            while True:
                resp = client.documents.list(
                    container_tags=[container],
                    limit=100,
                    page=page,
                    include_content=False,
                )
                memories = getattr(resp, "memories", []) or []
                if not memories:
                    break
                for mem in memories:
                    total += 1
                    meta = getattr(mem, "metadata", {}) or {}
                    name = meta.get("source_name", "")
                    if name:
                        bucket.add(name)
                pagination = getattr(resp, "pagination", None)
                total_pages = int(getattr(pagination, "total_pages", 1) or 1)
                if page >= total_pages:
                    break
                page += 1
        except Exception:
            break

    return {
        "total_chunks": total,
        "pdf_sources": sorted(pdf_sources),
        "whatsapp_sources": sorted(whatsapp_sources),
        "supermemory_available": True,
    }
